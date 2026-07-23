import uuid
from typing import Any
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.observability import log_operation, step_completed
from app.llm.orchestrator import LLMOrchestrator
from app.models.interview.interview_evaluation import InterviewEvaluation
from app.models.interview.interview_message import InterviewMessage
from app.models.interview.interview_session import InterviewSession
from app.models.interview.interview_turn_analysis import InterviewTurnAnalysis
from app.services.interview.evaluation_config import (
    EVALUATION_WEIGHTS,
    QUALITY_SCORE_MAPPING,
    RECOMMENDATION_THRESHOLDS,
    SKILL_NAME_MAPPINGS,
)
from app.services.interview.evaluation_context import EvaluationContext
from app.services.interview.evaluation_prompt_builder import EvaluationPromptBuilder
from app.shared.enums import InterviewMessageRole, QuestionType, SessionStatus


class QuestionReviewItem(BaseModel):
    message_id: str
    ideal_answer: str
    evaluation: str
    strengths: list[str]
    improvements: list[str]


class EvaluationSynthesisSchema(BaseModel):
    summary: str
    timeline_reviews: list[QuestionReviewItem]


class EvaluationService:
    """Orchestrates score aggregation, hiring recommendation evaluation,
    LLM qualitative synthesis, and evaluation persistence.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.orchestrator = LLMOrchestrator()
        self.prompt_builder = EvaluationPromptBuilder()

    @log_operation(category="INTERVIEW", name="Evaluation Generation")
    async def generate_evaluation(self, session_id: uuid.UUID) -> InterviewEvaluation:
        """Deterministically calculate interview evaluation scores, query LLM for qualitative reviews, and persist."""
        # 1. Idempotency Check
        stmt_eval = select(InterviewEvaluation).filter(InterviewEvaluation.session_id == session_id)
        existing_eval = await self.db.scalar(stmt_eval)
        if existing_eval:
            step_completed("INTERVIEW", "Evaluation loaded from cache (idempotent)")
            return existing_eval

        # 2. Fetch Session & Validate Status
        stmt_session = select(InterviewSession).filter(InterviewSession.id == session_id)
        session = await self.db.scalar(stmt_session)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview session not found",
            )

        # 3. Load Messages and Turn Analyses
        stmt_msgs = (
            select(InterviewMessage)
            .filter(InterviewMessage.session_id == session_id)
            .order_by(InterviewMessage.sequence_number.asc())
        )
        msgs_seq = await self.db.scalars(stmt_msgs)
        history = list(msgs_seq.all())

        stmt_analyses = (
            select(InterviewTurnAnalysis)
            .join(InterviewMessage)
            .filter(InterviewMessage.session_id == session_id)
        )
        analyses_seq = await self.db.scalars(stmt_analyses)
        analyses = list(analyses_seq.all())

        category = session.interview_category
        category_name = category.value.upper()

        # 4. Deterministically Aggregate Dimension Scores (0 - 100)
        # Find candidate responses that have evaluations
        analyses_by_msg = {str(a.message_id): a for a in analyses}
        candidate_turns = [m for m in history if m.role == InterviewMessageRole.CANDIDATE]

        dimension_totals: dict[str, float] = {}
        dimension_counts: dict[str, int] = {}
        
        # Initialize dimensions
        weights = EVALUATION_WEIGHTS.get(category_name, EVALUATION_WEIGHTS["TECHNICAL"])
        for dimension in weights.keys():
            dimension_totals[dimension] = 0.0
            dimension_counts[dimension] = 0

        # Sum turn observations
        for turn in candidate_turns:
            msg_id_str = str(turn.id)
            if msg_id_str in analyses_by_msg:
                a = analyses_by_msg[msg_id_str]
                for dimension in weights.keys():
                    val = getattr(a, dimension, "N/A")
                    if val != "N/A" and val in QUALITY_SCORE_MAPPING:
                        dimension_totals[dimension] += QUALITY_SCORE_MAPPING[val]
                        dimension_counts[dimension] += 1

        # Calculate dimension averages
        dimension_averages: dict[str, float] = {}
        for dimension in weights.keys():
            count = dimension_counts[dimension]
            # Use neutral 70.0 if no turns were evaluated for this dimension
            dimension_averages[dimension] = (
                dimension_totals[dimension] / count if count > 0 else 70.0
            )

        # Calculate dynamic skill scores (mapped to 1 - 5 star scale)
        skill_scores: dict[str, float] = {}
        skill_mappings = SKILL_NAME_MAPPINGS.get(category_name, SKILL_NAME_MAPPINGS["TECHNICAL"])
        for display_name, dimension in skill_mappings.items():
            avg_score = dimension_averages.get(dimension, 70.0)
            skill_scores[display_name] = round(avg_score / 20.0, 2)

        # Compute dynamic overall score (0 - 100)
        overall_score_float = 0.0
        for dimension, weight in weights.items():
            overall_score_float += dimension_averages.get(dimension, 70.0) * weight
        overall_score = min(max(0, int(round(overall_score_float))), 100)

        # 5. Determine Hiring Recommendation from thresholds
        recommendation = "Borderline Hire"
        for item in RECOMMENDATION_THRESHOLDS:
            if item["min"] <= overall_score <= item["max"]:
                recommendation = item["recommendation"]
                break

        # 6. Calculate Turn-by-Turn Question Scores & Map Question Numbers
        turn_scores: dict[str, int] = {}
        q_number_map: dict[str, int] = {}
        q_idx = 1

        for i, msg in enumerate(history):
            msg_id_str = str(msg.id)
            if msg.role == InterviewMessageRole.INTERVIEWER:
                if msg.question_type in (
                    QuestionType.PRIMARY.value,
                    QuestionType.FOLLOW_UP.value,
                    QuestionType.CLARIFICATION.value,
                ):
                    q_number_map[msg_id_str] = q_idx
                    q_idx += 1
            elif msg.role == InterviewMessageRole.CANDIDATE:
                # Find preceding interviewer question
                prev_q_id = None
                for m_prev in reversed(history[:i]):
                    if m_prev.role == InterviewMessageRole.INTERVIEWER:
                        prev_q_id = str(m_prev.id)
                        break

                if msg_id_str in analyses_by_msg and prev_q_id:
                    a = analyses_by_msg[msg_id_str]
                    turn_score_val = 0.0
                    for dimension, weight in weights.items():
                        val = getattr(a, dimension, "N/A")
                        mapped_val = QUALITY_SCORE_MAPPING.get(val, 70)
                        turn_score_val += mapped_val * weight
                    turn_scores[prev_q_id] = min(max(0, int(round(turn_score_val))), 100)

        # 7. Generate Synthesis via single LLM call
        summary = None
        timeline_reviews = []

        if history:
            # Format Context
            context = EvaluationContext(
                session_id=str(session_id),
                interview_category=category.value,
                overall_score=overall_score,
                recommendation=recommendation,
                skill_scores=skill_scores,
                transcript=[
                    {
                        "id": str(m.id),
                        "role": m.role.value if hasattr(m.role, "value") else str(m.role),
                        "content": m.content,
                        "question_type": m.question_type,
                    }
                    for m in history
                ],
                turn_analyses=[
                    {
                        "message_id": str(a.message_id),
                        "technical_accuracy": a.technical_accuracy,
                        "depth": a.depth,
                        "coverage": a.coverage,
                        "communication": a.communication,
                        "confidence": a.confidence,
                        "strengths": a.strengths,
                        "missing_topics": a.missing_topics,
                    }
                    for a in analyses
                ],
            )

            # Build prompts
            system_prompt, user_prompt = self.prompt_builder.build_prompts(context)

            # Call LLM Orchestrator
            synthesis_result: EvaluationSynthesisSchema = (
                await self.orchestrator.structured_completion(
                    profile="interview_evaluation",
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_model=EvaluationSynthesisSchema,
                )
            )

            summary = synthesis_result.summary
            for item in synthesis_result.timeline_reviews:
                timeline_reviews.append(
                    {
                        "question_id": item.message_id,
                        "question_number": q_number_map.get(item.message_id, 1),
                        "score": turn_scores.get(item.message_id, 70),
                        "ideal_answer": item.ideal_answer,
                        "evaluation": item.evaluation,
                        "strengths": item.strengths,
                        "improvements": item.improvements,
                    }
                )

        # 8. Persist and return evaluation
        evaluation = InterviewEvaluation(
            session_id=session_id,
            overall_score=overall_score,
            recommendation=recommendation,
            summary=summary,
            timeline_reviews=timeline_reviews,
            skill_scores=skill_scores,
            evaluation_version="v1",
        )
        self.db.add(evaluation)
        await self.db.commit()

        step_completed("INTERVIEW", "Evaluation successfully synthesized and stored")
        return evaluation

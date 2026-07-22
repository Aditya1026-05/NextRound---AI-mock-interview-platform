from collections.abc import Sequence

import structlog
from pydantic import BaseModel

from app.models.interview.interview_message import InterviewMessage
from app.schemas.interview.interview_analysis import InterviewAnalysis
from app.shared.enums import (
    AnswerQuality,
    DifficultyLevel,
    InterviewAction,
    InterviewState,
    QuestionType,
)

logger = structlog.get_logger()


class InterviewDecision(BaseModel):
    """Pydantic model representing deterministic backend decision for interview progression."""

    action: InterviewAction
    next_difficulty: DifficultyLevel
    should_transition: bool
    next_state: InterviewState | None = None
    question_type: QuestionType
    reason: str


class InterviewDecisionEngine:
    """Decision engine executing deterministic logic mapping turn observations to interview states, difficulty level transitions, and sections advancement."""

    def decide_next_step(
        self,
        analysis: InterviewAnalysis,
        current_state: InterviewState,
        current_section_index: int,
        current_difficulty: DifficultyLevel,
        blueprint_json: dict | None,
        history: Sequence[InterviewMessage],
    ) -> InterviewDecision:
        # 1. Handle non-in-progress state transitions
        if current_state == InterviewState.GREETING:
            return InterviewDecision(
                action=InterviewAction.NEXT_QUESTION,
                next_difficulty=current_difficulty,
                should_transition=True,
                next_state=InterviewState.INTRODUCTION,
                question_type=QuestionType.INTRODUCTION,
                reason="Greeting finished, request candidate introduction.",
            )

        if current_state == InterviewState.INTRODUCTION:
            return InterviewDecision(
                action=InterviewAction.NEXT_QUESTION,
                next_difficulty=current_difficulty,
                should_transition=True,
                next_state=InterviewState.IN_PROGRESS,
                question_type=QuestionType.PRIMARY,
                reason="Introduction finished, transition to active blueprint sections.",
            )

        if current_state == InterviewState.CLOSING:
            return InterviewDecision(
                action=InterviewAction.NEXT_QUESTION,
                next_difficulty=current_difficulty,
                should_transition=True,
                next_state=InterviewState.COMPLETED,
                question_type=QuestionType.CLOSING,
                reason="Closing finished, complete the session.",
            )

        if current_state == InterviewState.COMPLETED:
            return InterviewDecision(
                action=InterviewAction.NEXT_QUESTION,
                next_difficulty=current_difficulty,
                should_transition=False,
                next_state=InterviewState.COMPLETED,
                question_type=QuestionType.CLOSING,
                reason="Interview is already completed.",
            )

        # 2. In-Progress logic
        # Resolve dynamic limits
        min_questions = 2
        max_questions = 4
        max_followups = 2

        if blueprint_json and "sections" in blueprint_json:
            sections = blueprint_json.get("sections", [])
            if 0 <= current_section_index < len(sections):
                sec = sections[current_section_index]
                min_questions = sec.get("min_questions", 2)
                max_questions = sec.get("max_questions", 4)
                max_followups = sec.get("max_followups", 2)

        # Calculate question and follow-up counts for the current section index.
        # Find candidate replies since the start of the current section (the most recent PRIMARY or TRANSITION question).
        primary_question_idx = -1
        for i in range(len(history) - 1, -1, -1):
            msg = history[i]
            if msg.role == "INTERVIEWER" and msg.question_type in (
                QuestionType.PRIMARY.value,
                QuestionType.TRANSITION.value,
            ):
                primary_question_idx = i
                break

        if primary_question_idx != -1:
            candidate_replies_in_sec = [
                m for m in history[primary_question_idx:] if m.role == "CANDIDATE"
            ]
            question_count = len(candidate_replies_in_sec)
        else:
            # Fallback if no primary found (e.g. at the absolute start of IN_PROGRESS)
            candidate_replies_in_sec = []
            question_count = 0

        # Follow-up questions are any questions after the primary in the same section.
        followup_count = max(0, question_count - 1)

        logger.info(
            "Decision Engine processing turn variables",
            section_index=current_section_index,
            question_count=question_count,
            followup_count=followup_count,
            min_questions=min_questions,
            max_questions=max_questions,
            max_followups=max_followups,
        )

        # 3. Resolve gradual difficulty transition
        next_difficulty = current_difficulty
        if (
            analysis.technical_accuracy == AnswerQuality.EXCELLENT
            and analysis.depth == AnswerQuality.EXCELLENT
        ):
            if current_difficulty == DifficultyLevel.EASY:
                next_difficulty = DifficultyLevel.MEDIUM
            elif current_difficulty == DifficultyLevel.MEDIUM:
                next_difficulty = DifficultyLevel.HARD
        elif analysis.technical_accuracy == AnswerQuality.POOR:
            if current_difficulty == DifficultyLevel.HARD:
                next_difficulty = DifficultyLevel.MEDIUM
            elif current_difficulty == DifficultyLevel.MEDIUM:
                next_difficulty = DifficultyLevel.EASY

        # 4. Resolve next action and state transitions
        if analysis.communication == AnswerQuality.POOR:
            return InterviewDecision(
                action=InterviewAction.CLARIFY,
                next_difficulty=next_difficulty,
                should_transition=False,
                question_type=QuestionType.CLARIFICATION,
                reason="Poor communication detected. Asking for clarification.",
            )

        # Follow up on missing topics if budget permits and limits not reached,
        # but NOT if the candidate replied poorly (e.g. they don't know / don't remember).
        if (
            len(analysis.missing_topics) > 0
            and followup_count < max_followups
            and question_count < max_questions
            and analysis.technical_accuracy != AnswerQuality.POOR
            and analysis.depth != AnswerQuality.POOR
        ):
            return InterviewDecision(
                action=InterviewAction.FOLLOW_UP,
                next_difficulty=next_difficulty,
                should_transition=False,
                question_type=QuestionType.FOLLOW_UP,
                reason=f"Missing concepts detected ({', '.join(analysis.missing_topics)}). Follow-up initiated.",
            )

        # Transition section if question limit reached, or min questions met with good/excellent coverage,
        # OR if min questions met and candidate's answers show poor accuracy/depth (avoiding robotic grilling).
        if question_count >= max_questions or (
            question_count >= min_questions
            and (
                analysis.coverage in (AnswerQuality.EXCELLENT, AnswerQuality.GOOD)
                or analysis.technical_accuracy == AnswerQuality.POOR
                or analysis.depth == AnswerQuality.POOR
            )
        ):
            return InterviewDecision(
                action=InterviewAction.SECTION_COMPLETE,
                next_difficulty=next_difficulty,
                should_transition=True,
                question_type=QuestionType.TRANSITION,
                reason="Blueprint section complete. Advancing section index or state.",
            )

        # Otherwise, ask the next primary question in this section
        return InterviewDecision(
            action=InterviewAction.NEXT_QUESTION,
            next_difficulty=next_difficulty,
            should_transition=False,
            question_type=QuestionType.PRIMARY,
            reason="Continue current blueprint section with next primary question.",
        )

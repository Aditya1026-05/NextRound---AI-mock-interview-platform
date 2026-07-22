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
        section_active_seconds: float = 0.0,
        session_active_seconds: float = 0.0,
        session_duration_minutes: int = 45,
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

        # 4.5. Resolve Session Timeout (Force transition to CLOSING if total duration exceeded)
        is_session_time_up = session_active_seconds >= session_duration_minutes * 60.0
        if is_session_time_up:
            return InterviewDecision(
                action=InterviewAction.SECTION_COMPLETE,
                next_difficulty=next_difficulty,
                should_transition=True,
                next_state=InterviewState.CLOSING,
                question_type=QuestionType.TRANSITION,
                reason="Total interview session duration expired. Transitioning to CLOSING.",
            )

        # 5. Resolve Section Transitions (Proportional Time-gated & Safety Rails)
        blueprint_total = 60.0
        if blueprint_json:
            blueprint_total = float(blueprint_json.get("estimated_duration", 60.0))
            if blueprint_total <= 0.0:
                blueprint_total = 60.0

        sec_duration_raw = 15.0
        if blueprint_json and "sections" in blueprint_json:
            sections = blueprint_json.get("sections", [])
            if 0 <= current_section_index < len(sections):
                sec = sections[current_section_index]
                sec_duration_raw = float(sec.get("duration", 15.0))

        # Calculate proportional duration relative to session_duration_minutes
        proportion = sec_duration_raw / blueprint_total
        section_duration_seconds = proportion * session_duration_minutes * 60.0

        is_time_up = section_active_seconds >= section_duration_seconds
        is_limit_reached = question_count >= 5
        is_llm_transition_request = getattr(analysis, "should_transition_section", False) and question_count >= min_questions

        if is_time_up or is_limit_reached or is_llm_transition_request:
            reason = "Time limit reached." if is_time_up else ("Hard safety question limit reached." if is_limit_reached else "LLM transition request approved.")
            return InterviewDecision(
                action=InterviewAction.SECTION_COMPLETE,
                next_difficulty=next_difficulty,
                should_transition=True,
                question_type=QuestionType.TRANSITION,
                reason=f"Blueprint section complete. {reason} Advancing section index or state.",
            )

        # 6. Resolve Topic Transitions (Internally switching projects/topics)
        is_llm_topic_change = getattr(analysis, "should_transition_topic", False)
        is_followup_limit_reached = followup_count >= max_followups

        if is_llm_topic_change or is_followup_limit_reached:
            reason = "LLM topic change requested." if is_llm_topic_change else "Follow-up question budget reached."
            return InterviewDecision(
                action=InterviewAction.CHANGE_TOPIC,
                next_difficulty=next_difficulty,
                should_transition=False,
                question_type=QuestionType.PRIMARY,
                reason=f"Change project/topic: {reason}",
            )

        # 7. Resolve Follow-up (Drilling down if budget and criteria permit)
        if (
            len(analysis.missing_topics) > 0
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

        # Otherwise, ask the next primary question in this section
        return InterviewDecision(
            action=InterviewAction.NEXT_QUESTION,
            next_difficulty=next_difficulty,
            should_transition=False,
            question_type=QuestionType.PRIMARY,
            reason="Continue current blueprint section with next primary question.",
        )

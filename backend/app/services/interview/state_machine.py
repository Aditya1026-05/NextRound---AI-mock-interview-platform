from typing import ClassVar

import structlog

from app.models.interview.interview_message import InterviewMessage
from app.models.interview.interview_session import InterviewSession
from app.shared.enums import InterviewMessageRole, InterviewState

logger = structlog.get_logger()


class InvalidStateTransitionError(Exception):
    """Raised when an invalid interview state transition is requested."""
    pass


class InterviewStateMachine:
    """Manages interview conversation flow state transitions and blueprint progressions."""

    VALID_TRANSITIONS: ClassVar[dict[InterviewState, set[InterviewState]]] = {
        InterviewState.READY: {InterviewState.GREETING},
        InterviewState.GREETING: {InterviewState.INTRODUCTION},
        InterviewState.INTRODUCTION: {InterviewState.IN_PROGRESS},
        InterviewState.IN_PROGRESS: {InterviewState.IN_PROGRESS, InterviewState.CLOSING},
        InterviewState.CLOSING: {InterviewState.COMPLETED},
        InterviewState.COMPLETED: set(),
    }

    def validate_transition(self, current: InterviewState, target: InterviewState) -> None:
        """Enforces type-safe valid transition boundaries."""
        if target not in self.VALID_TRANSITIONS.get(current, set()):
            raise InvalidStateTransitionError(
                f"Invalid transition from {current} to {target}"
            )

    def advance_state(
        self,
        session: InterviewSession,
        history: list[InterviewMessage],
        total_sections: int,
    ) -> tuple[InterviewState, int | None]:
        """Inspects current state, section indexes, and history turns to determine
        the next valid interview state and section progress.
        """
        current_state = InterviewState(session.interview_state)
        current_section = session.current_section_index or 0

        # Filter messages into interviewer questions vs candidate replies
        candidate_replies = [m for m in history if m.role == InterviewMessageRole.CANDIDATE]

        if current_state == InterviewState.READY:
            # First turn: start interview transitions to greeting
            return InterviewState.GREETING, 0

        elif current_state == InterviewState.GREETING:
            # Transition to introduction once candidate responds to greeting
            if len(candidate_replies) >= 1:
                return InterviewState.INTRODUCTION, 0
            return InterviewState.GREETING, 0

        elif current_state == InterviewState.INTRODUCTION:
            # Transition to in_progress once candidate responds to introduction
            # (which means at least 2 responses total: 1 for greeting, 1 for intro)
            if len(candidate_replies) >= 2:
                if total_sections > 0:
                    return InterviewState.IN_PROGRESS, 0
                else:
                    return InterviewState.CLOSING, None
            return InterviewState.INTRODUCTION, 0

        elif current_state == InterviewState.IN_PROGRESS:
            # Count replies since entering IN_PROGRESS
            # The first 2 replies were for GREETING and INTRODUCTION
            in_progress_replies = candidate_replies[2:]
            
            # Dynamically calculate the expected replies to reach/complete the current section.
            # Proportional allocation: 1 turn (question+answer) per 4 minutes of section duration, min 2, max 5.
            expected_total_replies_for_current = 0
            if session.blueprint and session.blueprint.blueprint_json:
                sections = session.blueprint.blueprint_json.get("sections", [])
                for i in range(current_section + 1):
                    if i < len(sections):
                        duration = sections[i].get("duration", 10)
                        sec_turns = max(2, min(5, int(duration / 4)))
                        expected_total_replies_for_current += sec_turns
            else:
                expected_total_replies_for_current = (current_section + 1) * 2

            if len(in_progress_replies) >= expected_total_replies_for_current:
                next_section = current_section + 1
                if next_section < total_sections:
                    logger.info(
                        "Advancing blueprint section index",
                        current_section=current_section,
                        next_section=next_section,
                        total_sections=total_sections,
                    )
                    return InterviewState.IN_PROGRESS, next_section
                else:
                    logger.info("All blueprint sections completed. Transitioning to CLOSING.")
                    return InterviewState.CLOSING, None
            
            return InterviewState.IN_PROGRESS, current_section

        elif current_state == InterviewState.CLOSING:
            # Finalize session to COMPLETED once candidate answers closing statement
            # Number of candidate replies expected: 2 (greeting+intro) + sum of section turns + 1 (closing)
            expected_replies_to_complete = 2 + 1
            if session.blueprint and session.blueprint.blueprint_json:
                sections = session.blueprint.blueprint_json.get("sections", [])
                for sec in sections:
                    duration = sec.get("duration", 10)
                    expected_replies_to_complete += max(2, min(5, int(duration / 4)))
            else:
                expected_replies_to_complete += total_sections * 2

            if len(candidate_replies) >= expected_replies_to_complete:
                return InterviewState.COMPLETED, None
            return InterviewState.CLOSING, None

        return current_state, current_section


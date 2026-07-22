from typing import ClassVar

import structlog

from app.models.interview.interview_session import InterviewSession
from app.shared.enums import InterviewState

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
        action: str,
        should_transition: bool,
        next_state_override: str | None = None,
    ) -> tuple[InterviewState, int | None]:
        """Validates state transition requested by decision engine and calculates next state/section."""
        current_state = InterviewState(session.interview_state)
        current_section = session.current_section_index

        total_sections = 0
        if session.blueprint and session.blueprint.blueprint_json:
            total_sections = len(session.blueprint.blueprint_json.get("sections", []))

        if not should_transition:
            return current_state, current_section

        # Determine target next state
        next_state = current_state
        next_section = current_section

        if next_state_override:
            next_state = InterviewState(next_state_override)
            if next_state != current_state:
                if next_state not in self.VALID_TRANSITIONS.get(current_state, set()):
                    raise InvalidStateTransitionError(
                        f"Illegal transition requested from {current_state} to {next_state}"
                    )
            # If entering IN_PROGRESS, initialize section index to 0
            if next_state == InterviewState.IN_PROGRESS:
                next_section = 0
            # If entering CLOSING or COMPLETED, section index is None
            elif next_state in (InterviewState.CLOSING, InterviewState.COMPLETED):
                next_section = None

        elif current_state == InterviewState.IN_PROGRESS and action == "SECTION_COMPLETE":
            # Move to next blueprint section or transition to CLOSING
            next_sec_idx = (current_section or 0) + 1
            if next_sec_idx < total_sections:
                next_state = InterviewState.IN_PROGRESS
                next_section = next_sec_idx
                logger.info(
                    "Advancing blueprint section index",
                    current_section=current_section,
                    next_section=next_section,
                    total_sections=total_sections,
                )
            else:
                next_state = InterviewState.CLOSING
                next_section = None
                logger.info("All blueprint sections completed. Transitioning to CLOSING.")

        return next_state, next_section

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.observability import (
    bind_context,
    log_operation,
    step_completed,
    step_failed,
)
from app.models.interview.interview_session import InterviewSession
from app.services.interview.conversation_service import ConversationService
from app.services.interview.interviewer_agent import InterviewerAgent
from app.services.interview.prompt_builder import InterviewPromptBuilder
from app.services.interview.state_machine import InterviewStateMachine
from app.shared.enums import InterviewMessageRole, InterviewState, SessionStatus

logger = structlog.get_logger()


class InterviewEngine:
    """Orchestrates mock interview conversation flow by coordinating history fetches,
    state progressions, prompt building, and model generations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.conversation_service = ConversationService(db)
        self.state_machine = InterviewStateMachine()
        self.prompt_builder = InterviewPromptBuilder()
        self.interviewer_agent = InterviewerAgent()

    @log_operation(category="INTERVIEW", name="Interview Engine Turn Execution")
    async def generate_next_turn(self, session_id: uuid.UUID) -> str:
        """Advance interview states, generate prompts, invoke LLM, and persist AI response."""
        # 1. Fetch the session
        stmt = select(InterviewSession).filter(InterviewSession.id == session_id)
        session = await self.db.scalar(stmt)
        if not session:
            step_failed("VALIDATION", "Session loading", f"Session not found: {session_id}")
            raise ValueError("Session not found")

        bind_context(
            session_id=str(session.id),
            user_id=str(session.user_id),
            resume_id=str(session.resume_id) if session.resume_id else None,
        )

        # 2. Fetch recent conversation history
        history = await self.conversation_service.load_recent_history(session_id)

        # 3. Resolve active sections count
        total_sections = 0
        if session.blueprint and session.blueprint.blueprint_json:
            total_sections = len(session.blueprint.blueprint_json.get("sections", []))

        # 4. Advance State
        old_state = session.interview_state
        old_section = session.current_section_index

        next_state, next_section = self.state_machine.advance_state(
            session, list(history), total_sections
        )

        # Validate transition constraints
        self.state_machine.validate_transition(InterviewState(old_state), next_state)

        # Update model properties
        session.interview_state = next_state.value
        session.current_section_index = next_section

        if next_state == InterviewState.COMPLETED:
            session.status = SessionStatus.COMPLETED

        await self.db.flush()

        if old_state != next_state.value or old_section != next_section:
            logger.info(
                f"Interview State Transitioned: {old_state} -> {next_state.value} (Section: {old_section} -> {next_section})",
                category="INTERVIEW",
                old_state=old_state,
                next_state=next_state.value,
                old_section=old_section,
                next_section=next_section,
            )

        if next_state == InterviewState.COMPLETED:
            final_msg = "The interview is now completed. Thank you for your time."
            await self.conversation_service.save_message(
                session_id=session.id,
                role=InterviewMessageRole.INTERVIEWER,
                content=final_msg,
            )
            return final_msg

        # 5. Build prompt context
        memory_ctx = await self.conversation_service.load_summary(session_id)
        prompt_ctx = self.prompt_builder.build_prompts(session, list(history), memory_ctx)
        step_completed("INTERVIEW", "Prompt context built")

        # 6. Generate response from agent
        logger.info("Invoking Interviewer Agent", category="INTERVIEW")
        response_text = await self.interviewer_agent.generate_response(prompt_ctx)
        step_completed("INTERVIEW", "Interviewer Agent response generated")

        # 7. Persist generated message
        await self.conversation_service.save_message(
            session_id=session.id,
            role=InterviewMessageRole.INTERVIEWER,
            content=response_text,
        )
        step_completed("INTERVIEW", "Interviewer Agent response saved")

        return response_text

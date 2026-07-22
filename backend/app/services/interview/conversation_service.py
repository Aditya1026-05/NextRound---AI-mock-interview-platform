import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview.interview_message import InterviewMessage
from app.shared.enums import InterviewMessageRole


class ConversationService:
    """Service responsible for interview chat message persistence and retrieval."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def next_sequence_number(self, session_id: uuid.UUID) -> int:
        """Fetch the next available sequence number for the conversation."""
        stmt = select(func.max(InterviewMessage.sequence_number)).filter(
            InterviewMessage.session_id == session_id
        )
        max_seq = await self.db.scalar(stmt)
        return 0 if max_seq is None else max_seq + 1

    async def save_message(
        self,
        session_id: uuid.UUID,
        role: InterviewMessageRole,
        content: str,
        sequence_number: int | None = None,
        question_type: str | None = None,
    ) -> InterviewMessage:
        """Persist a message turn to the database."""
        if sequence_number is None:
            sequence_number = await self.next_sequence_number(session_id)

        msg = InterviewMessage(
            session_id=session_id,
            role=role,
            content=content,
            sequence_number=sequence_number,
            question_type=question_type,
        )
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def load_full_history(self, session_id: uuid.UUID) -> Sequence[InterviewMessage]:
        """Load the complete sequence of messages for a session."""
        stmt = select(InterviewMessage).filter(
            InterviewMessage.session_id == session_id
        ).order_by(InterviewMessage.sequence_number.asc())
        result = await self.db.scalars(stmt)
        return result.all()

    async def load_recent_history(
        self, session_id: uuid.UUID, limit: int = 20
    ) -> Sequence[InterviewMessage]:
        """Load recent sequence of messages for a session.
        For Phase 5.2.1, this returns the full history, but satisfies the structural signature.
        """
        return await self.load_full_history(session_id)

    async def load_summary(self, session_id: uuid.UUID) -> str | None:
        """Load consolidations of chat turns. Returns None in Phase 5.2.1."""
        return None

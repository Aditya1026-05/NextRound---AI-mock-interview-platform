import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.interview.interview_session import InterviewSession


class InterviewEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """InterviewEvent model storing candidate telemetry keystrokes and editor events."""

    __tablename__ = "interview_events"

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    elapsed_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    event_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Relationships
    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="events", lazy="selectin"
    )

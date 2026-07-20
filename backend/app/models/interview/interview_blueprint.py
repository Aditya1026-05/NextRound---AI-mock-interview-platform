import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.interview.interview_session import InterviewSession


class InterviewBlueprint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """InterviewBlueprint model storing the generated technical outline/agenda of a session."""

    __tablename__ = "interview_blueprints"

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    estimated_duration: Mapped[int] = mapped_column(Integer, nullable=False)
    blueprint_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Generation Observability Metadata
    generated_by_profile: Mapped[str] = mapped_column(String(100), nullable=False)
    generated_model: Mapped[str] = mapped_column(String(100), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    # Relationship
    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession",
        back_populates="blueprint",
        foreign_keys=[session_id],
    )

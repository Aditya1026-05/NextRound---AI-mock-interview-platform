import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.interview.interview_message import InterviewMessage


class InterviewTurnAnalysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """InterviewTurnAnalysis model storing factual evaluation observations for candidate response turns."""

    __tablename__ = "interview_turn_analyses"

    message_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interview_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    technical_accuracy: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    depth: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    coverage: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    communication: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    confidence: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    missing_topics: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    strengths: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    difficulty_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    blueprint_section: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    analysis_version: Mapped[str] = mapped_column(
        String(10),
        default="v1",
        nullable=False,
    )

    message: Mapped["InterviewMessage"] = relationship(
        "InterviewMessage",
        lazy="selectin",
    )

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.interview.interview_session import InterviewSession


class InterviewEvaluation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """InterviewEvaluation model storing final reports, summaries, dynamic skills and timeline reviews."""

    __tablename__ = "interview_evaluations"

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    timeline_reviews: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    skill_scores: Mapped[dict[str, float]] = mapped_column(JSONB, nullable=False)
    evaluation_version: Mapped[str] = mapped_column(
        String(10), default="v1", nullable=False
    )

    # Relationship
    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession",
        back_populates="evaluation",
        foreign_keys=[session_id],
    )

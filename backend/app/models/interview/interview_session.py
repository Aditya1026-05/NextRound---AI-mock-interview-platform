import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.enums import EndedReasonType, SessionStatus
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.identity.user import User
    from app.models.interview.interview_competency_score import (
        InterviewCompetencyScore,
    )
    from app.models.interview.interview_event import InterviewEvent
    from app.models.interview.interview_question import InterviewQuestion
    from app.models.interview.interview_template import InterviewTemplate
    from app.models.resume.resume import Resume


class InterviewSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """InterviewSession model storing mock interview execution states and parameters."""

    __tablename__ = "interview_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interview_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, native_enum=True),
        default=SessionStatus.IDLE,
        nullable=False,
    )
    ended_reason: Mapped[EndedReasonType | None] = mapped_column(
        Enum(EndedReasonType, native_enum=True), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_duration_seconds: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")
    template: Mapped["InterviewTemplate"] = relationship(
        "InterviewTemplate", lazy="selectin"
    )
    resume: Mapped["Resume"] = relationship("Resume", lazy="selectin")

    questions: Mapped[list["InterviewQuestion"]] = relationship(
        "InterviewQuestion",
        back_populates="session",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    events: Mapped[list["InterviewEvent"]] = relationship(
        "InterviewEvent",
        back_populates="session",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    competency_scores: Mapped[list["InterviewCompetencyScore"]] = relationship(
        "InterviewCompetencyScore",
        back_populates="session",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

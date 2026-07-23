import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.enums import (
    DifficultyType,
    EndedReasonType,
    InterviewCategory,
    InterviewRole,
    InterviewState,
    SessionStatus,
)
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.ai.candidate_profile import CandidateProfile
    from app.models.identity.user import User
    from app.models.interview.interview_blueprint import InterviewBlueprint
    from app.models.interview.interview_evaluation import InterviewEvaluation
    from app.models.interview.interview_competency_score import (
        InterviewCompetencyScore,
    )
    from app.models.interview.interview_event import InterviewEvent
    from app.models.interview.interview_message import InterviewMessage
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
        default=SessionStatus.CREATED,
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
    total_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Added columns for Phase 5.1
    candidate_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    interview_category: Mapped[InterviewCategory] = mapped_column(
        Enum(InterviewCategory, native_enum=False), nullable=False
    )
    role: Mapped[InterviewRole | None] = mapped_column(
        Enum(InterviewRole, native_enum=False), nullable=True
    )
    difficulty: Mapped[DifficultyType] = mapped_column(
        Enum(DifficultyType, native_enum=False),
        default=DifficultyType.ADAPTIVE,
        nullable=False,
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    interview_state: Mapped[InterviewState] = mapped_column(
        Enum(InterviewState, native_enum=False),
        default=InterviewState.READY,
        nullable=False,
    )
    current_section_index: Mapped[int | None] = mapped_column(
        Integer, default=0, nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")
    template: Mapped["InterviewTemplate"] = relationship(
        "InterviewTemplate", lazy="selectin"
    )
    resume: Mapped["Resume"] = relationship("Resume", lazy="selectin")
    candidate_profile: Mapped["CandidateProfile | None"] = relationship(
        "CandidateProfile", lazy="selectin"
    )
    messages: Mapped[list["InterviewMessage"]] = relationship(
        "InterviewMessage",
        back_populates="session",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="InterviewMessage.sequence_number",
    )
    blueprint: Mapped["InterviewBlueprint | None"] = relationship(
        "InterviewBlueprint",
        back_populates="session",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    evaluation: Mapped["InterviewEvaluation | None"] = relationship(
        "InterviewEvaluation",
        back_populates="session",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )

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

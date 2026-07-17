import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.interview.competency import Competency
    from app.models.interview.interview_session import InterviewSession


class InterviewCompetencyScore(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """InterviewCompetencyScore model storing candidate evaluation ratings."""

    __tablename__ = "interview_competency_scores"

    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "competency_id",
            name="uq_interview_competency_scores_session_id_competency_id",
        ),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("competencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="competency_scores", lazy="selectin"
    )
    competency: Mapped["Competency"] = relationship(
        "Competency", back_populates="scores", lazy="selectin"
    )

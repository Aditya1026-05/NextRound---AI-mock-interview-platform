from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.interview.interview_competency_score import (
        InterviewCompetencyScore,
    )
    from app.models.interview.question_competency import QuestionCompetency


class Competency(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Competency model representing assessment rubrics (e.g. Communication, DSA)."""

    __tablename__ = "competencies"

    name: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    question_competencies: Mapped[list["QuestionCompetency"]] = relationship(
        "QuestionCompetency",
        back_populates="competency",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    scores: Mapped[list["InterviewCompetencyScore"]] = relationship(
        "InterviewCompetencyScore",
        back_populates="competency",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

from typing import TYPE_CHECKING

from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.enums import DifficultyType, InterviewType
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.interview.question_competency import QuestionCompetency
    from app.models.interview.question_test_case import QuestionTestCase


class QuestionBank(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """QuestionBank model storing preset/default question definitions."""

    __tablename__ = "question_bank"

    __mapper_args__ = {
        "polymorphic_on": "question_type",
    }

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[InterviewType] = mapped_column(
        Enum(InterviewType, native_enum=True), nullable=False
    )
    difficulty: Mapped[DifficultyType] = mapped_column(
        Enum(DifficultyType, native_enum=True), nullable=False
    )
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    question_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    test_cases: Mapped[list["QuestionTestCase"]] = relationship(
        "QuestionTestCase",
        back_populates="question",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    competencies: Mapped[list["QuestionCompetency"]] = relationship(
        "QuestionCompetency",
        back_populates="question",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

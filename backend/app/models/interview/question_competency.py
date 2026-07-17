import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.interview.competency import Competency
    from app.models.interview.question_bank import QuestionBank


class QuestionCompetency(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """QuestionCompetency association model mapping questions to competencies."""

    __tablename__ = "question_competencies"

    __table_args__ = (
        UniqueConstraint(
            "question_bank_id",
            "competency_id",
            name="uq_question_competencies_question_bank_id_competency_id",
        ),
    )

    question_bank_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("question_bank.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("competencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Relationships
    question: Mapped["QuestionBank"] = relationship(
        "QuestionBank", back_populates="competencies", lazy="selectin"
    )
    competency: Mapped["Competency"] = relationship(
        "Competency", back_populates="question_competencies", lazy="selectin"
    )

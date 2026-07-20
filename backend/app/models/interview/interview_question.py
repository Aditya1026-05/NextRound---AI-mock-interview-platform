import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.enums import InterviewType
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.interview.interview_response import InterviewResponse
    from app.models.interview.interview_session import InterviewSession
    from app.models.interview.question_bank import QuestionBank


class InterviewQuestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """InterviewQuestion model storing copies of session questions."""

    __tablename__ = "interview_questions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_question_bank_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("question_bank.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[InterviewType] = mapped_column(
        Enum(InterviewType, native_enum=True), nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_by_ai: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    generation_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="questions", lazy="selectin"
    )
    original_question: Mapped["QuestionBank"] = relationship(
        "QuestionBank", lazy="selectin"
    )
    responses: Mapped[list["InterviewResponse"]] = relationship(
        "InterviewResponse",
        back_populates="question",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

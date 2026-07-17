import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.enums import ResponseType
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.interview.interview_question import InterviewQuestion


class InterviewResponse(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """InterviewResponse model storing candidate submitted transcriptions or code."""

    __tablename__ = "interview_responses"

    interview_question_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    response_type: Mapped[ResponseType] = mapped_column(
        Enum(ResponseType, native_enum=True), nullable=False
    )
    response_content: Mapped[str] = mapped_column(Text, nullable=False)
    audio_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    programming_language: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    transcript_confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    # Relationships
    question: Mapped["InterviewQuestion"] = relationship(
        "InterviewQuestion", back_populates="responses", lazy="selectin"
    )

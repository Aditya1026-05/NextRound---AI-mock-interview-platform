import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.interview.question_bank import QuestionBank


class QuestionTestCase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """QuestionTestCase model storing test cases for coding compilation validation."""

    __tablename__ = "question_test_cases"

    question_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("question_bank.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    input: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    is_sample: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    is_hidden: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    time_limit_ms: Mapped[int] = mapped_column(
        Integer, default=2000, server_default=text("2000"), nullable=False
    )
    memory_limit_kb: Mapped[int] = mapped_column(
        Integer,
        default=128000,
        server_default=text("128000"),
        nullable=False,
    )

    # Relationships
    question: Mapped["QuestionBank"] = relationship(
        "QuestionBank", back_populates="test_cases", lazy="selectin"
    )

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Enum, ForeignKey, Integer, String, Text, Float, Boolean, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.enums import SubmissionSource, ExecutionType
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.interview.interview_session import InterviewSession
    from app.models.interview.coding_problem import CodingProblem


class CodeSubmission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """CodeSubmission model storing candidate code executions and submission attempts."""

    __tablename__ = "code_submissions"

    session_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    coding_problem_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("question_bank.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    problem_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    submitted_code: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    execution_type: Mapped[ExecutionType] = mapped_column(
        Enum(ExecutionType, native_enum=True), nullable=False
    )
    is_final_submission: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    submission_source: Mapped[SubmissionSource] = mapped_column(
        Enum(SubmissionSource, native_enum=True), nullable=False
    )
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    language_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    provider_submission_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    passed_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    total_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    execution_time_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default=text("0.0"))
    memory_kb: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)
    compile_output: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    session: Mapped["InterviewSession | None"] = relationship(
        "InterviewSession", lazy="selectin"
    )
    coding_problem: Mapped["QuestionBank"] = relationship(
        "QuestionBank", foreign_keys=[coding_problem_id], lazy="selectin"
    )

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.enums import DifficultyType, InterviewType
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.interview.company import Company
    from app.models.interview.role import Role


class InterviewTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """InterviewTemplate model storing preset interview path parameters."""

    __tablename__ = "interview_templates"

    company_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    difficulty: Mapped[DifficultyType] = mapped_column(
        Enum(DifficultyType, native_enum=True), nullable=False
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    interview_type: Mapped[InterviewType] = mapped_column(
        Enum(InterviewType, native_enum=True), nullable=False
    )
    resume_required: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    max_questions: Mapped[int] = mapped_column(
        Integer, default=5, server_default=text("5"), nullable=False
    )
    passing_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship("Company", lazy="selectin")
    role: Mapped["Role"] = relationship("Role", lazy="selectin")

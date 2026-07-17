import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.resume.education import Education
    from app.models.resume.project import Project
    from app.models.resume.skill import Skill
    from app.models.resume.work_experience import WorkExperience


class Resume(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Resume database model representing candidate resume metadata and parse text."""

    __tablename__ = "resumes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )

    # Relationships
    education: Mapped[list["Education"]] = relationship(
        "Education",
        back_populates="resume",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    work_experiences: Mapped[list["WorkExperience"]] = relationship(
        "WorkExperience",
        back_populates="resume",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="resume",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    skills: Mapped[list["Skill"]] = relationship(
        "Skill",
        secondary="resume_skills",
        back_populates="resumes",
        lazy="selectin",
    )

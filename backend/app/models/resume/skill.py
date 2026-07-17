import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.resume.project import Project
    from app.models.resume.resume import Resume
    from app.models.resume.skill_category import SkillCategory


class Skill(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Skill model representing a specific tool or competency (e.g. React, Python)."""

    __tablename__ = "skills"

    category_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skill_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )

    # Relationships
    category: Mapped["SkillCategory"] = relationship(
        "SkillCategory", back_populates="skills", lazy="selectin"
    )
    resumes: Mapped[list["Resume"]] = relationship(
        "Resume",
        secondary="resume_skills",
        back_populates="skills",
        lazy="selectin",
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        secondary="project_skills",
        back_populates="skills",
        lazy="selectin",
    )

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.resume.resume import Resume
    from app.models.resume.skill import Skill


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Project history model representing software or candidate side-projects."""

    __tablename__ = "projects"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Relationships
    resume: Mapped["Resume"] = relationship(
        "Resume", back_populates="projects", lazy="selectin"
    )
    skills: Mapped[list["Skill"]] = relationship(
        "Skill",
        secondary="project_skills",
        back_populates="projects",
        lazy="selectin",
    )

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ResumeSkill(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """ResumeSkill association database model for many-to-many relationship."""

    __tablename__ = "resume_skills"

    __table_args__ = (
        UniqueConstraint(
            "resume_id", "skill_id", name="uq_resume_skills_resume_id_skill_id"
        ),
    )

    resume_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

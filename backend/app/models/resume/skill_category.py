
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.resume.skill import Skill


class SkillCategory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Skill category model representing technology disciplines.

    Examples include Frontend, Backend, etc.
    """

    __tablename__ = "skill_categories"

    name: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )

    # Relationships
    skills: Mapped[list["Skill"]] = relationship(
        "Skill",
        back_populates="category",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

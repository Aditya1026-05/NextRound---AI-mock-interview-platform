import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.identity.user import User
    from app.models.resume.resume import Resume


class CandidateProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """CandidateProfile database model representing structured AI-generated candidate intelligence."""

    __tablename__ = "candidate_profiles"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Relationships
    resume: Mapped["Resume"] = relationship("Resume", lazy="selectin")
    user: Mapped["User"] = relationship("User", lazy="selectin")

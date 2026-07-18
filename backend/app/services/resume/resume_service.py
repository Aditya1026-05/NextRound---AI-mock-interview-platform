import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume.resume import Resume
from app.schemas.resume.ai import UploadMetadata
from app.shared.enums.resume import ResumeStatus


class ResumeService:
    """Service responsible for managing database records for user resumes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_resume_record(
        self,
        user_id: uuid.UUID,
        metadata: UploadMetadata,
        raw_text: str | None,
        status: ResumeStatus,
    ) -> Resume:
        """Create a new Resume database record from upload metadata and parsed text."""
        # Query if this user already has any other resumes
        stmt = select(func.count()).select_from(Resume).filter(
            Resume.user_id == user_id
        )
        existing_count = await self.db.scalar(stmt) or 0
        is_primary = existing_count == 0

        # Create model instance
        resume = Resume(
            user_id=user_id,
            file_url=metadata.file_url,
            original_filename=metadata.original_filename,
            mime_type=metadata.mime_type,
            file_size=metadata.file_size,
            status=status,
            raw_text=raw_text,
            parsed_json=None,
            is_primary=is_primary,
        )

        self.db.add(resume)
        await self.db.commit()
        await self.db.refresh(resume)
        return resume

import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai.candidate_profile import CandidateProfile
from app.models.interview.interview_session import InterviewSession
from app.models.resume.resume import Resume
from app.services.interview.blueprint_service import BlueprintService
from app.shared.enums import (
    DifficultyType,
    InterviewCategory,
    InterviewRole,
    ResumeStatus,
    SessionStatus,
)

logger = structlog.get_logger()


class InterviewSessionService:
    """Service responsible for establishing interview sessions, running validations, and initiating AI blueprinting."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.blueprint_service = BlueprintService(db)

    async def create_session(
        self,
        user_id: uuid.UUID,
        resume_id: uuid.UUID,
        category: InterviewCategory,
        role: InterviewRole | None,
    ) -> InterviewSession:
        """Atomically validate resume, category/role options, initialize CREATED session, generate blueprint, and transition to READY."""
        # 1. Resolve default category durations
        if category == InterviewCategory.TECHNICAL:
            duration_minutes = 45
            # Validate role exists for technical category
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Role is required for Technical interviews",
                )
        elif category == InterviewCategory.CODING:
            duration_minutes = 60
            role = None  # Role is not applicable/ignored
        elif category == InterviewCategory.BEHAVIORAL:
            duration_minutes = 30
            role = None  # Role is not applicable/ignored
        elif category == InterviewCategory.SYSTEM_DESIGN:
            duration_minutes = 60
            role = None  # Role is not applicable/ignored
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid interview category: {category}",
            )

        logger.info(
            "Creating interview session",
            user_id=user_id,
            resume_id=resume_id,
            category=category,
            role=role,
            duration=duration_minutes,
        )

        # 2. Fetch and validate resume (ownership and status)
        stmt_resume = select(Resume).filter(
            Resume.id == resume_id, Resume.user_id == user_id
        )
        resume = await self.db.scalar(stmt_resume)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found or access unauthorized",
            )

        if resume.status != ResumeStatus.CONFIRMED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Resume confirmation required. Current status: {resume.status}",
            )

        # 3. Fetch candidate profile
        stmt_cp = select(CandidateProfile).filter(
            CandidateProfile.resume_id == resume_id
        )
        candidate_profile = await self.db.scalar(stmt_cp)
        if not candidate_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate Profile not found. Please confirm the resume again.",
            )

        # Retrieve summary block from candidate profile JSON
        profile_json = candidate_profile.profile_json or {}
        summary = profile_json.get("summary") or profile_json.get(
            "overall_technical_profile", ""
        )

        # 4. Initialize session in CREATED status
        session = InterviewSession(
            user_id=user_id,
            resume_id=resume_id,
            candidate_profile_id=candidate_profile.id,
            interview_category=category,
            role=role,
            difficulty=DifficultyType.ADAPTIVE,
            duration_minutes=duration_minutes,
            status=SessionStatus.CREATED,
        )
        self.db.add(session)
        await self.db.flush()

        try:
            # 5. Generate and persist blueprint (handles deleting existing internally)
            await self.blueprint_service.create_blueprint(session, summary)

            # 6. Update session status to READY
            session.status = SessionStatus.READY
            await self.db.flush()

            # 7. Commit transaction
            await self.db.commit()
            await self.db.refresh(session, ["blueprint"])

            logger.info(
                "Interview session initialized and READY",
                session_id=session.id,
                status=session.status,
            )
            return session

        except Exception as e:
            logger.error("Blueprint generation failed. Rolling back session creation.", error=str(e))
            await self.db.rollback()
            raise e

import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.observability import bind_context, log_operation
from app.models.ai.candidate_profile import CandidateProfile
from app.models.interview.interview_session import InterviewSession
from app.models.resume.resume import Resume
from app.services.interview.blueprint_service import BlueprintService
from app.shared.enums import (
    DifficultyType,
    EndedReasonType,
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

    @log_operation(category="INTERVIEW", name="Interview Session Creation")
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
            duration_minutes = 60
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

        from app.core.observability import (
            step_completed,
            step_failed,
            transaction_committed,
            transaction_rolled_back,
            transaction_started,
        )

        bind_context(resume_id=resume_id, user_id=user_id)

        # 2. Fetch and validate resume (ownership and status)
        stmt_resume = select(Resume).filter(
            Resume.id == resume_id, Resume.user_id == user_id
        )
        resume = await self.db.scalar(stmt_resume)
        if not resume:
            step_failed("VALIDATION", "Resume ownership verification", "Resume not found or unauthorized")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found or access unauthorized",
            )

        if resume.status != ResumeStatus.CONFIRMED:
            step_failed("VALIDATION", "Resume ownership verification", f"Resume status: {resume.status}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Resume confirmation required. Current status: {resume.status}",
            )

        step_completed("VALIDATION", "Resume ownership verified")

        # 3. Fetch candidate profile
        stmt_cp = select(CandidateProfile).filter(
            CandidateProfile.resume_id == resume_id
        )
        candidate_profile = await self.db.scalar(stmt_cp)
        if not candidate_profile:
            step_failed("VALIDATION", "Candidate profile verification", "Candidate profile not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate Profile not found. Please confirm the resume again.",
            )

        step_completed("VALIDATION", "Candidate profile located")

        # Retrieve summary block from candidate profile JSON
        profile_json = candidate_profile.profile_json or {}
        summary = profile_json.get("summary") or profile_json.get(
            "overall_technical_profile", ""
        )

        # 3.5 Clean up and finalize any active sessions for this user (lag/midway close safety)
        stmt_active = select(InterviewSession).filter(
            InterviewSession.user_id == user_id,
            InterviewSession.status.in_([SessionStatus.CREATED, SessionStatus.READY, SessionStatus.IN_PROGRESS])
        )
        active_sessions = await self.db.scalars(stmt_active)
        for act_sess in active_sessions.all():
            act_sess.status = SessionStatus.COMPLETED
            act_sess.ended_reason = EndedReasonType.USER_LEFT
            if act_sess.overall_score is None:
                act_sess.overall_score = 0.0

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
        bind_context(session_id=str(session.id), candidate_profile_id=str(candidate_profile.id))
        step_completed("INTERVIEW", "Session created")

        transaction_started()
        try:
            # 5. Generate and persist blueprint (handles deleting existing internally)
            await self.blueprint_service.create_blueprint(session, summary)
            step_completed("INTERVIEW", "Blueprint generated")

            # 6. Update session status to READY
            session.status = SessionStatus.READY
            await self.db.flush()

            # 7. Commit transaction
            await self.db.commit()
            transaction_committed()
            await self.db.refresh(session, ["blueprint"])

            step_completed("INTERVIEW", "Session READY")
            return session

        except Exception as e:
            transaction_rolled_back(e)
            await self.db.rollback()
            raise e

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.dependencies.providers import get_db
from app.models.identity.user import User
from app.models.interview.interview_session import InterviewSession
from app.services.interview.session_service import InterviewSessionService
from app.shared.enums import (
    DifficultyType,
    InterviewCategory,
    InterviewRole,
    SessionStatus,
)

router = APIRouter()
logger = structlog.get_logger()


# Schemas
class InterviewSessionCreate(BaseModel):
    resume_id: uuid.UUID
    category: InterviewCategory
    role: InterviewRole | None = None


class InterviewSessionCreateResponse(BaseModel):
    session_id: uuid.UUID
    status: SessionStatus
    blueprint_generated: bool


class InterviewSessionDetailResponse(BaseModel):
    id: uuid.UUID
    category: InterviewCategory
    role: InterviewRole | None
    difficulty: DifficultyType
    duration_minutes: int
    status: SessionStatus
    resume_filename: str
    blueprint_title: str | None = None


@router.post(
    "/session",
    response_model=InterviewSessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new mock interview session and generate AI blueprint",
)
async def create_session(
    payload: InterviewSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Validate resume configuration, create an interview session in CREATED state, run blueprinting, and mark READY."""
    session_service = InterviewSessionService(db)
    try:
        session = await session_service.create_session(
            user_id=current_user.id,
            resume_id=payload.resume_id,
            category=payload.category,
            role=payload.role,
        )
        return InterviewSessionCreateResponse(
            session_id=session.id,
            status=session.status,
            blueprint_generated=(session.blueprint is not None),
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(
            "API failed to create interview session",
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interview session preparation failed: {e!s}",
        ) from e


@router.get(
    "/session/{session_id}",
    response_model=InterviewSessionDetailResponse,
    summary="Retrieve session configuration details for the Waiting Room",
)
async def get_session_detail(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details for a specific interview session, ensuring user ownership."""
    stmt = (
        select(InterviewSession)
        .filter(InterviewSession.id == session_id, InterviewSession.user_id == current_user.id)
    )
    session = await db.scalar(stmt)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found",
        )

    # Resolve resume original filename
    resume_name = session.resume.original_filename if session.resume else "Unknown Resume"

    # Resolve blueprint title
    blueprint_title = session.blueprint.title if session.blueprint else None

    return InterviewSessionDetailResponse(
        id=session.id,
        category=session.interview_category,
        role=session.role,
        difficulty=session.difficulty,
        duration_minutes=session.duration_minutes,
        status=session.status,
        resume_filename=resume_name,
        blueprint_title=blueprint_title,
    )

import uuid
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.dependencies.providers import get_db
from app.models.identity.user import User
from app.models.interview.interview_session import InterviewSession
from app.models.interview.interview_message import InterviewMessage
from app.services.interview.session_service import InterviewSessionService
from app.shared.enums import (
    DifficultyType,
    InterviewCategory,
    InterviewRole,
    SessionStatus,
)
from app.schemas.interview.interview_evaluation import (
    InterviewEvaluationResponseSchema,
    TimelineReviewResponseSchema,
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
    started_at: datetime | None = None


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
        started_at=session.started_at,
    )


# New schemas for conversational flow


class InterviewStartResponse(BaseModel):
    message: str
    interview_state: str
    session_status: SessionStatus


class InterviewRespondRequest(BaseModel):
    message: str


class InterviewRespondResponse(BaseModel):
    message: str
    interview_state: str
    session_status: SessionStatus


class MessageResponseSchema(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    sequence_number: int
    created_at: datetime


@router.post(
    "/session/{session_id}/start",
    response_model=InterviewStartResponse,
    summary="Start the interview session and get the interviewer's greeting",
)
async def start_interview(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Validate ownership, status, and generate first greeting."""
    stmt = select(InterviewSession).filter(
        InterviewSession.id == session_id, InterviewSession.user_id == current_user.id
    )
    session = await db.scalar(stmt)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found",
        )

    if session.status != SessionStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start interview in status: {session.status}",
        )

    # Set status to IN_PROGRESS and start
    from datetime import timezone
    session.status = SessionStatus.IN_PROGRESS
    session.started_at = datetime.now(timezone.utc)
    await db.flush()

    from app.services.interview.interview_engine import InterviewEngine
    engine = InterviewEngine(db)
    try:
        greeting = await engine.generate_next_turn(session_id)
        await db.commit()
        await db.refresh(session)
        return InterviewStartResponse(
            message=greeting,
            interview_state=session.interview_state,
            session_status=session.status,
        )
    except Exception as e:
        logger.error("Failed to start interview conversation", session_id=session_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start interview: {e!s}",
        ) from e


@router.post(
    "/session/{session_id}/respond",
    response_model=InterviewRespondResponse,
    summary="Submit candidate response and receive next interviewer turn",
)
async def respond_interview(
    session_id: uuid.UUID,
    payload: InterviewRespondRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Save candidate response, run InterviewEngine, and return interviewer response."""
    stmt = select(InterviewSession).filter(
        InterviewSession.id == session_id, InterviewSession.user_id == current_user.id
    )
    session = await db.scalar(stmt)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found",
        )

    if session.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Interview is not in progress. Status: {session.status}",
        )

    clean_msg = payload.message.strip()
    if not clean_msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Response message content cannot be empty",
        )

    from app.services.interview.conversation_service import ConversationService
    from app.services.interview.interview_engine import InterviewEngine
    from app.shared.enums import InterviewMessageRole

    conv_service = ConversationService(db)
    engine = InterviewEngine(db)

    try:
        # Save user response
        await conv_service.save_message(
            session_id=session_id,
            role=InterviewMessageRole.CANDIDATE,
            content=clean_msg,
        )

        # Generate next interviewer turn
        reply = await engine.generate_next_turn(session_id)
        await db.commit()
        await db.refresh(session)

        return InterviewRespondResponse(
            message=reply,
            interview_state=session.interview_state,
            session_status=session.status,
        )
    except Exception as e:
        logger.error("Failed to generate interviewer reply", session_id=session_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interviewer response generation failed: {e!s}",
        ) from e


@router.get(
    "/session/{session_id}/messages",
    response_model=list[MessageResponseSchema],
    summary="Retrieve full conversation history for this session",
)
async def get_session_messages(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all persisted chat messages for the interview session."""
    stmt = select(InterviewSession).filter(
        InterviewSession.id == session_id, InterviewSession.user_id == current_user.id
    )
    session = await db.scalar(stmt)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found",
        )

    from app.services.interview.conversation_service import ConversationService
    conv_service = ConversationService(db)
    history = await conv_service.load_full_history(session_id)
    return [
        MessageResponseSchema(
            id=m.id,
            role=m.role,
            content=m.content,
            sequence_number=m.sequence_number,
            created_at=m.created_at,
        )
        for m in history
    ]


@router.post(
    "/session/{session_id}/evaluate",
    response_model=InterviewEvaluationResponseSchema,
    summary="Generate and persist evaluation report for a completed session",
)
async def evaluate_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Evaluate an interview session, synthesizing qualitative and quantitative metrics."""
    # First verify ownership
    stmt = select(InterviewSession).filter(
        InterviewSession.id == session_id, InterviewSession.user_id == current_user.id
    )
    session = await db.scalar(stmt)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found",
        )

    from app.services.interview.evaluation_service import EvaluationService
    service = EvaluationService(db)
    evaluation = await service.generate_evaluation(session_id)

    # Convert database model timeline reviews into response schema format
    stmt_msgs = (
        select(InterviewMessage)
        .filter(InterviewMessage.session_id == session_id)
    )
    msgs_seq = await db.scalars(stmt_msgs)
    msgs_map = {str(m.id): m for m in msgs_seq.all()}

    from app.shared.enums import InterviewMessageRole
    timeline_responses = []
    for item in evaluation.timeline_reviews:
        q_id = item.get("question_id")
        q_msg = msgs_map.get(str(q_id))
        
        q_content = q_msg.content if q_msg else "Unknown Question"
        a_content = "No Answer Provided"
        if q_msg:
            candidate_reply = None
            for m in msgs_map.values():
                if m.role == InterviewMessageRole.CANDIDATE and m.sequence_number == q_msg.sequence_number + 1:
                    candidate_reply = m
                    break
            if candidate_reply:
                a_content = candidate_reply.content

        timeline_responses.append(
            TimelineReviewResponseSchema(
                question=q_content,
                answer=a_content,
                score=item.get("score", 70),
                ideal_answer=item.get("ideal_answer", ""),
                evaluation=item.get("evaluation", ""),
                strengths=item.get("strengths", []),
                improvements=item.get("improvements", []),
            )
        )

    from app.schemas.interview.interview_evaluation import InterviewEvaluationResponseSchema
    return InterviewEvaluationResponseSchema(
        id=evaluation.id,
        session_id=evaluation.session_id,
        overall_score=evaluation.overall_score,
        recommendation=evaluation.recommendation,
        summary=evaluation.summary,
        skill_scores=evaluation.skill_scores,
        timeline_reviews=timeline_responses,
        evaluation_version=evaluation.evaluation_version,
    )


@router.get(
    "/session/{session_id}/evaluation",
    response_model=InterviewEvaluationResponseSchema,
    summary="Retrieve existing evaluation report for a session",
)
async def get_session_evaluation(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the evaluation report if it has been generated."""
    # First verify ownership
    stmt_session = select(InterviewSession).filter(
        InterviewSession.id == session_id, InterviewSession.user_id == current_user.id
    )
    session = await db.scalar(stmt_session)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found",
        )

    from app.models.interview.interview_evaluation import InterviewEvaluation
    stmt_eval = select(InterviewEvaluation).filter(InterviewEvaluation.session_id == session_id)
    evaluation = await db.scalar(stmt_eval)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation has not been generated for this session",
        )

    stmt_msgs = select(InterviewMessage).filter(InterviewMessage.session_id == session_id)
    msgs_seq = await db.scalars(stmt_msgs)
    msgs_map = {str(m.id): m for m in msgs_seq.all()}

    from app.shared.enums import InterviewMessageRole
    timeline_responses = []
    for item in evaluation.timeline_reviews:
        q_id = item.get("question_id")
        q_msg = msgs_map.get(str(q_id))
        
        q_content = q_msg.content if q_msg else "Unknown Question"
        a_content = "No Answer Provided"
        if q_msg:
            candidate_reply = None
            for m in msgs_map.values():
                if m.role == InterviewMessageRole.CANDIDATE and m.sequence_number == q_msg.sequence_number + 1:
                    candidate_reply = m
                    break
            if candidate_reply:
                a_content = candidate_reply.content

        timeline_responses.append(
            TimelineReviewResponseSchema(
                question=q_content,
                answer=a_content,
                score=item.get("score", 70),
                ideal_answer=item.get("ideal_answer", ""),
                evaluation=item.get("evaluation", ""),
                strengths=item.get("strengths", []),
                improvements=item.get("improvements", []),
            )
        )

    from app.schemas.interview.interview_evaluation import InterviewEvaluationResponseSchema
    return InterviewEvaluationResponseSchema(
        id=evaluation.id,
        session_id=evaluation.session_id,
        overall_score=evaluation.overall_score,
        recommendation=evaluation.recommendation,
        summary=evaluation.summary,
        skill_scores=evaluation.skill_scores,
        timeline_reviews=timeline_responses,
        evaluation_version=evaluation.evaluation_version,
    )

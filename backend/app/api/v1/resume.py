import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.core.storage import LocalStorageProvider
from app.dependencies.providers import get_db
from app.models.identity.user import User
from app.schemas.resume.ai import (
    ParsedResumeResponse,
    ResumeListItem,
    RenameResumeRequest,
)
from app.services.resume.extraction_service import ExtractionService
from app.services.resume.parser_service import ResumeParserService
from app.services.resume.resume_service import ResumeService
from app.services.resume.upload_service import MAX_FILE_SIZE, ResumeUploadService
from app.shared.enums.resume import ResumeStatus

import uuid
from sqlalchemy import select
from app.models.resume.resume import Resume

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "",
    response_model=ParsedResumeResponse | None,
    summary="Get candidate's latest parsed resume profile",
)
async def get_latest_resume(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch user's most recent resume record from database."""
    stmt = (
        select(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
        .limit(1)
    )
    resume = await db.scalar(stmt)
    if not resume:
        return None

    if resume.status == ResumeStatus.FAILED:
        return None

    if resume.parsed_json:
        try:
            parsed_obj = ParsedResumeResponse.model_validate(resume.parsed_json)
            parsed_obj.resume_id = resume.id
            parsed_obj.status = resume.status
            return parsed_obj
        except Exception as e:
            logger.error("Failed to parse stored resume JSON", error=str(e))
            return None

    return ParsedResumeResponse(
        resume_id=resume.id,
        status=resume.status,
        full_name=None,
        summary=None,
        education=[],
        work_experiences=[],
        projects=[],
        skills=[],
        certifications=[],
        achievements=[],
        confidence_score=None,
        parser_provider="gemini",
        parser_model="gemini-2.5-flash",
    )


@router.get(
    "/list",
    response_model=list[ResumeListItem],
    summary="List all candidate's resume profiles",
)
async def list_resumes(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch all resume records for the authenticated candidate."""
    stmt = (
        select(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
    )
    resumes = await db.scalars(stmt)
    result = []
    for r in resumes:
        result.append(
            ResumeListItem(
                id=r.id,
                filename=r.original_filename,
                status=r.status,
                created_at=r.created_at.isoformat(),
                is_primary=r.is_primary,
            )
        )
    return result


@router.get(
    "/{resume_id}",
    response_model=ParsedResumeResponse,
    summary="Get a specific parsed resume profile by ID",
)
async def get_resume_by_id(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a specific resume record by UUID."""
    stmt = select(Resume).filter(
        Resume.id == resume_id, Resume.user_id == current_user.id
    )
    resume = await db.scalar(stmt)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    if resume.parsed_json:
        try:
            parsed_obj = ParsedResumeResponse.model_validate(resume.parsed_json)
            parsed_obj.resume_id = resume.id
            parsed_obj.status = resume.status
            return parsed_obj
        except Exception as e:
            logger.error("Failed to parse stored resume JSON", error=str(e))

    return ParsedResumeResponse(
        resume_id=resume.id,
        status=resume.status,
        full_name=None,
        summary=None,
        education=[],
        work_experiences=[],
        projects=[],
        skills=[],
        certifications=[],
        achievements=[],
        confidence_score=None,
        parser_provider="gemini",
        parser_model="gemini-2.5-flash",
    )


@router.patch(
    "/{resume_id}/rename",
    response_model=ResumeListItem,
    summary="Rename a specific resume profile",
)
async def rename_resume(
    resume_id: uuid.UUID,
    request: RenameResumeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the filename/custom name of a candidate's resume."""
    stmt = select(Resume).filter(
        Resume.id == resume_id, Resume.user_id == current_user.id
    )
    resume = await db.scalar(stmt)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    resume.original_filename = request.filename
    await db.commit()
    await db.refresh(resume)

    return ResumeListItem(
        id=resume.id,
        filename=resume.original_filename,
        status=resume.status,
        created_at=resume.created_at.isoformat(),
        is_primary=resume.is_primary,
    )


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a candidate's resume profile",
)
async def delete_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a specific resume record owned by the candidate."""
    stmt = select(Resume).filter(
        Resume.id == resume_id, Resume.user_id == current_user.id
    )
    resume = await db.scalar(stmt)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    await db.delete(resume)
    await db.commit()


@router.post(
    "/manual",
    response_model=ParsedResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a blank manual resume draft profile",
)
async def create_manual_resume(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Initialize an empty resume record for manual editing."""
    initial_json = {
        "full_name": "",
        "summary": "",
        "education": [],
        "work_experiences": [],
        "projects": [],
        "skills": [],
        "certifications": [],
        "achievements": [],
        "confidence_score": 1.0,
        "parser_provider": "manual",
        "parser_model": "manual",
        "parser_version": "1.0",
    }
    resume = Resume(
        user_id=current_user.id,
        file_url="manual",
        original_filename="New Manual Profile",
        mime_type="application/json",
        file_size=0,
        status=ResumeStatus.REVIEW_PENDING,
        raw_text="",
        parsed_json=initial_json,
        is_primary=False,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    # Validate output
    parsed_obj = ParsedResumeResponse.model_validate(initial_json)
    parsed_obj.resume_id = resume.id
    parsed_obj.status = resume.status
    return parsed_obj


@router.put(
    "/{resume_id}",
    response_model=ParsedResumeResponse,
    summary="Update a candidate's resume draft details",
)
async def update_resume_draft(
    resume_id: uuid.UUID,
    request: ParsedResumeResponse,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the parsed_json field of a candidate's resume draft."""
    stmt = select(Resume).filter(
        Resume.id == resume_id, Resume.user_id == current_user.id
    )
    resume = await db.scalar(stmt)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    # Exclude resume_id and status from saved JSON to keep it clean
    dumped_data = request.model_dump()
    dumped_data.pop("resume_id", None)
    dumped_data.pop("status", None)

    resume.parsed_json = dumped_data
    await db.commit()
    await db.refresh(resume)

    parsed_obj = ParsedResumeResponse.model_validate(resume.parsed_json)
    parsed_obj.resume_id = resume.id
    parsed_obj.status = resume.status
    return parsed_obj


@router.post(
    "/upload",
    response_model=ParsedResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse a new candidate resume",
    description=(
        "Validate format/size, upload to storage, extract text, "
        "parse with LLM, and return structured review response."
    ),
)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Handle candidate resume upload, text extraction, and LLM structured parsing."""
    # 1. Read file content
    content = await file.read()
    filename = file.filename or "resume.pdf"
    content_type = file.content_type or ""

    # 2. Perform validations to raise proper HTTP exceptions
    # Size check
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10MB limit",
        )

    # Type check
    lower_name = filename.lower()
    is_pdf = lower_name.endswith(".pdf") and content_type == "application/pdf"
    is_docx = lower_name.endswith(".docx") and content_type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ]

    if not is_pdf and not is_docx:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file extension or MIME type",
        )

    # 3. Store file through upload service
    storage_provider = LocalStorageProvider()
    upload_service = ResumeUploadService(storage_provider=storage_provider)

    try:
        metadata = await upload_service.upload_file(
            content, filename, content_type
        )
    except Exception as e:
        logger.error("Failed to store file content", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store uploaded file",
        ) from e

    # 4. Attempt text extraction
    extraction_service = ExtractionService()
    extracted_text = None
    resume_service = ResumeService(db)

    try:
        extracted_text = await extraction_service.extract_text(
            content, content_type, filename
        )
    except Exception as e:
        logger.error(
            "Text extraction failed during resume ingestion",
            filename=filename,
            error=str(e),
        )
        # Ingest failed record
        await resume_service.create_resume_record(
            user_id=current_user.id,
            metadata=metadata,
            raw_text=None,
            status=ResumeStatus.FAILED,
            parsed_json=None,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Text extraction failed: {e!s}",
        ) from e

    # 5. Attempt LLM Parsing
    parser_service = ResumeParserService()
    try:
        parsed_obj = await parser_service.parse_resume(extracted_text)
    except Exception as e:
        logger.error(
            "AI parsing failed during resume ingestion",
            filename=filename,
            error=str(e),
        )
        # Create FAILED record with original raw text
        await resume_service.create_resume_record(
            user_id=current_user.id,
            metadata=metadata,
            raw_text=extracted_text,
            status=ResumeStatus.FAILED,
            parsed_json=None,
        )
        # Re-raise or wrap exception
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI parsing failed: {e!s}",
        ) from e

    # 6. Persist successful resume database record
    try:
        parsed_json = parsed_obj.model_dump(mode="json")
        resume = await resume_service.create_resume_record(
            user_id=current_user.id,
            metadata=metadata,
            raw_text=extracted_text,
            status=ResumeStatus.REVIEW_PENDING,
            parsed_json=parsed_json,
        )
    except Exception as e:
        logger.error("Failed to write resume database record", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register database record",
        ) from e

    # Populate identify fields in return schema
    parsed_obj.resume_id = resume.id
    parsed_obj.status = resume.status

    return parsed_obj

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.core.storage import LocalStorageProvider
from app.dependencies.providers import get_db
from app.models.identity.user import User
from app.schemas.resume.ai import ResumeUploadResponse
from app.services.resume.extraction_service import ExtractionService
from app.services.resume.resume_service import ResumeService
from app.services.resume.upload_service import MAX_FILE_SIZE, ResumeUploadService
from app.shared.enums.resume import ResumeStatus

router = APIRouter()
logger = structlog.get_logger()


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a new candidate resume",
    description="Validate format/size, upload to storage, and extract text.",
)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Handle candidate resume upload, filesystem persistence, and text extraction."""
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
    parsing_status = ResumeStatus.UPLOADED

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
        # Mark status as FAILED if text extraction fails
        parsing_status = ResumeStatus.FAILED

    # 5. Persist resume database record
    resume_service = ResumeService(db)
    try:
        resume = await resume_service.create_resume_record(
            user_id=current_user.id,
            metadata=metadata,
            raw_text=extracted_text,
            status=parsing_status,
        )
    except Exception as e:
        logger.error("Failed to write resume database record", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register database record",
        ) from e

    return ResumeUploadResponse(resume_id=resume.id, status=resume.status)

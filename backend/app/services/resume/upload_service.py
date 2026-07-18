from app.core.storage import StorageProvider
from app.schemas.resume.ai import UploadMetadata

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class ResumeUploadService:
    """Service to validate and upload file content via storage providers."""

    def __init__(self, storage_provider: StorageProvider):
        self.storage_provider = storage_provider

    async def upload_file(
        self, file_content: bytes, filename: str, mime_type: str
    ) -> UploadMetadata:
        """Validate file and persist through storage provider."""
        # 1. Size validations
        if len(file_content) == 0:
            raise ValueError("File is empty")

        if len(file_content) > MAX_FILE_SIZE:
            raise ValueError("File size exceeds 10MB limit")

        # 2. Extension & MIME Type validations
        lower_name = filename.lower()
        is_pdf = lower_name.endswith(".pdf") and mime_type == "application/pdf"
        is_docx = lower_name.endswith(".docx") and mime_type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ]

        if not is_pdf and not is_docx:
            raise ValueError("Invalid file extension or MIME type")

        # 3. Persistent upload
        return await self.storage_provider.upload_file(
            file_content, filename, mime_type
        )

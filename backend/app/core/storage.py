import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings
from app.schemas.resume.ai import UploadMetadata


class StorageProvider(ABC):
    """Abstract interface defining required storage provider behavior."""

    @abstractmethod
    async def upload_file(
        self, file_content: bytes, filename: str, mime_type: str
    ) -> UploadMetadata:
        """Upload file content to storage and return structured metadata."""
        pass


class LocalStorageProvider(StorageProvider):
    """Storage provider implementation targeting local filesystem storage."""

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)

    async def upload_file(
        self, file_content: bytes, filename: str, mime_type: str
    ) -> UploadMetadata:
        # Generate a unique filename using UUID prefix
        unique_prefix = uuid.uuid4().hex
        safe_filename = f"{unique_prefix}_{filename}"
        target_path = self.upload_dir / safe_filename

        # Write file content asynchronously or via sync write.
        # Running inside thread pool prevents event loop blocks.
        with open(target_path, "wb") as f:
            f.write(file_content)

        file_size = len(file_content)
        file_url = str(target_path)

        return UploadMetadata(
            file_url=file_url,
            original_filename=filename,
            mime_type=mime_type,
            file_size=file_size,
        )

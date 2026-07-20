import io

import docx
import fitz  # PyMuPDF
import structlog

logger = structlog.get_logger()


class ExtractionService:
    """Service responsible for extracting text from PDF and DOCX files."""

    async def extract_text(
        self, file_content: bytes, mime_type: str, filename: str
    ) -> str:
        """Extract clean text from PDF or DOCX binary stream."""
        is_pdf = mime_type == "application/pdf" or filename.lower().endswith(".pdf")
        is_docx = mime_type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ] or filename.lower().endswith(".docx")

        if not is_pdf and not is_docx:
            logger.error(
                "Unsupported file format for text extraction",
                mime_type=mime_type,
                filename=filename,
            )
            raise ValueError("Unsupported file format")

        try:
            if is_pdf:
                return await self._extract_pdf(file_content)
            else:
                return await self._extract_docx(file_content)
        except Exception as e:
            logger.error(
                "Failed to extract text from file",
                filename=filename,
                error=str(e),
            )
            raise

    async def _extract_pdf(self, file_content: bytes) -> str:
        text_list = []
        # Open PDF document from bytes stream
        with fitz.open(stream=file_content, filetype="pdf") as doc:
            for page in doc:
                page_text = page.get_text()
                if page_text:
                    text_list.append(page_text)
        return "\n".join(text_list).strip()

    async def _extract_docx(self, file_content: bytes) -> str:
        # Open DOCX document from bytes stream
        doc = docx.Document(io.BytesIO(file_content))
        text_list = []
        for paragraph in doc.paragraphs:
            if paragraph.text:
                text_list.append(paragraph.text)
        return "\n".join(text_list).strip()

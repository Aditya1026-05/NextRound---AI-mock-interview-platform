import io
import os
import uuid
from unittest.mock import patch

import docx
import fitz
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.dependencies.providers import get_db
from app.main import app
from app.schemas.resume.ai import ParsedResumeResponse
from app.shared.enums.resume import ResumeStatus


@pytest_asyncio.fixture
async def client(db):
    """Yield an AsyncClient with mocked database dependency override."""

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user_token(db):
    """Generate a test user and return their access token for request headers."""
    from app.core.security import create_access_token
    from app.models.identity.user import User

    # Create active user
    user = User(
        email=f"uploader_{uuid.uuid4().hex}@example.com",
        password_hash="hashed_password_123",
        full_name="Resume Uploader",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(subject=user.id)
    return token, user


def create_mock_pdf(text: str) -> bytes:
    """Dynamically generate a valid PDF bytes buffer containing text using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def create_mock_docx(text: str) -> bytes:
    """Generate a valid DOCX bytes buffer containing text using python-docx."""
    doc = docx.Document()
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
@patch("app.services.resume.parser_service.ResumeParserService.parse_resume")
async def test_upload_pdf_success(mock_parse, client, test_user_token):
    token, _user = test_user_token
    headers = {"Authorization": f"Bearer {token}"}
    pdf_content = create_mock_pdf("Candidate Resume text contents here")

    mock_parse.return_value = ParsedResumeResponse(
        resume_id=uuid.uuid4(),
        status=ResumeStatus.REVIEW_PENDING,
        full_name="Jane Doe",
        summary="Summary text",
        education=[],
        work_experiences=[],
        projects=[],
        skills=[],
        certifications=[],
        achievements=[],
        confidence_score=0.95,
        parser_provider="gemini",
        parser_model="gemini-2.5-flash",
    )

    files = {
        "file": (
            "resume_test.pdf",
            pdf_content,
            "application/pdf",
        )
    }

    response = await client.post(
        "/api/v1/resume/upload", headers=headers, files=files
    )
    assert response.status_code == 201

    data = response.json()
    assert "resume_id" in data
    assert data["status"] == ResumeStatus.REVIEW_PENDING

    # Verify file exists on disk
    assert os.path.exists(settings.UPLOAD_DIR)
    uploaded_files = os.listdir(settings.UPLOAD_DIR)
    assert any("resume_test.pdf" in f for f in uploaded_files)

    # Clean up uploaded files
    for f in uploaded_files:
        os.remove(os.path.join(settings.UPLOAD_DIR, f))


@pytest.mark.asyncio
@patch("app.services.resume.parser_service.ResumeParserService.parse_resume")
async def test_upload_docx_success(mock_parse, client, test_user_token):
    token, _user = test_user_token
    headers = {"Authorization": f"Bearer {token}"}
    docx_content = create_mock_docx("Candidate Resume DOCX text contents")

    mock_parse.return_value = ParsedResumeResponse(
        resume_id=uuid.uuid4(),
        status=ResumeStatus.REVIEW_PENDING,
        full_name="Jane Doe",
        summary="Summary text",
        education=[],
        work_experiences=[],
        projects=[],
        skills=[],
        certifications=[],
        achievements=[],
        confidence_score=0.95,
        parser_provider="gemini",
        parser_model="gemini-2.5-flash",
    )

    files = {
        "file": (
            "my_resume.docx",
            docx_content,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }

    response = await client.post(
        "/api/v1/resume/upload", headers=headers, files=files
    )
    assert response.status_code == 201

    data = response.json()
    assert "resume_id" in data
    assert data["status"] == ResumeStatus.REVIEW_PENDING

    # Verify file exists on disk
    uploaded_files = os.listdir(settings.UPLOAD_DIR)
    assert any("my_resume.docx" in f for f in uploaded_files)

    # Clean up
    for f in uploaded_files:
        os.remove(os.path.join(settings.UPLOAD_DIR, f))


@pytest.mark.asyncio
async def test_upload_invalid_extension(client, test_user_token):
    token, _ = test_user_token
    headers = {"Authorization": f"Bearer {token}"}

    files = {
        "file": (
            "hack.txt",
            b"unsupported content",
            "text/plain",
        )
    }

    response = await client.post(
        "/api/v1/resume/upload", headers=headers, files=files
    )
    assert response.status_code == 400
    assert "extension" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_invalid_mime_type(client, test_user_token):
    token, _ = test_user_token
    headers = {"Authorization": f"Bearer {token}"}
    pdf_content = create_mock_pdf("Resume text")

    files = {
        "file": (
            "valid_name.pdf",
            pdf_content,
            "image/png",  # Spoofed MIME
        )
    }

    response = await client.post(
        "/api/v1/resume/upload", headers=headers, files=files
    )
    assert response.status_code == 400
    assert "mime" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_oversized_file(client, test_user_token):
    token, _ = test_user_token
    headers = {"Authorization": f"Bearer {token}"}
    large_content = b"x" * (10 * 1024 * 1024 + 1)  # 10MB + 1B

    files = {
        "file": (
            "too_large.pdf",
            large_content,
            "application/pdf",
        )
    }

    response = await client.post(
        "/api/v1/resume/upload", headers=headers, files=files
    )
    assert response.status_code == 400
    assert "size" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_empty_file(client, test_user_token):
    token, _ = test_user_token
    headers = {"Authorization": f"Bearer {token}"}

    files = {
        "file": (
            "empty.pdf",
            b"",
            "application/pdf",
        )
    }

    response = await client.post(
        "/api/v1/resume/upload", headers=headers, files=files
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_unauthorized(client):
    pdf_content = create_mock_pdf("Unauthorized content")
    files = {
        "file": (
            "anon.pdf",
            pdf_content,
            "application/pdf",
        )
    }

    response = await client.post("/api/v1/resume/upload", files=files)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_provider_failure(client, test_user_token):
    token, _ = test_user_token
    headers = {"Authorization": f"Bearer {token}"}
    pdf_content = create_mock_pdf("Mock content")

    files = {
        "file": (
            "provider_fail.pdf",
            pdf_content,
            "application/pdf",
        )
    }

    # Mock upload_file of LocalStorageProvider to throw error
    with patch(
        "app.core.storage.LocalStorageProvider.upload_file",
        side_effect=Exception("Storage full"),
    ):
        response = await client.post(
            "/api/v1/resume/upload", headers=headers, files=files
        )
        assert response.status_code == 500
        assert "store" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_text_extraction_failure(client, test_user_token, db):
    token, _user = test_user_token
    headers = {"Authorization": f"Bearer {token}"}
    pdf_content = create_mock_pdf("Failing extraction text")

    files = {
        "file": (
            "extract_fail.pdf",
            pdf_content,
            "application/pdf",
        )
    }

    # Mock extract_text of ExtractionService to throw error
    with patch(
        "app.services.resume.extraction_service.ExtractionService.extract_text",
        side_effect=Exception("PDF parse error"),
    ):
        response = await client.post(
            "/api/v1/resume/upload", headers=headers, files=files
        )
        assert response.status_code == 400
        assert "extraction" in response.json()["detail"].lower()

        # Verify database has FAILED record
        from sqlalchemy import select

        from app.models.resume.resume import Resume

        stmt = select(Resume).filter(
            Resume.user_id == _user.id, Resume.status == ResumeStatus.FAILED
        )
        resume_db = await db.scalar(stmt)
        assert resume_db is not None
        assert resume_db.status == ResumeStatus.FAILED

        # Clean up files
        uploaded_files = os.listdir(settings.UPLOAD_DIR)
        for f in uploaded_files:
            os.remove(os.path.join(settings.UPLOAD_DIR, f))

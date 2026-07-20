import json
import os
import uuid
from unittest.mock import MagicMock, patch

import fitz
import litellm
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.exceptions import (
    AIProviderUnavailableException,
    InvalidAIResponseException,
)
from app.dependencies.providers import get_db
from app.llm.factory import LLMFactory
from app.main import app
from app.schemas.resume.ai import ParsedResumeResponse
from app.services.resume.parser_service import ResumeParserService
from app.shared.enums.resume import ResumeStatus


@pytest.fixture(autouse=True)
def mock_api_keys():
    """Autouse fixture to mock Gemini API keys for parsing tests."""
    from app.llm.registry import LLMRegistry, ProfileConfig

    mock_profile = ProfileConfig(primary="gemini-flash", fallbacks=[], retries=0)
    with (
        patch.object(settings, "GEMINI_API_KEY", "mock_key"),
        patch.object(settings, "LITELLM_GEMINI_API_KEY", "mock_key"),
        patch.object(settings, "LLM_FALLBACK_ORDER", ["gemini"]),
        patch.object(LLMRegistry, "get_profile", return_value=mock_profile),
    ):
        yield


@pytest_asyncio.fixture
async def client(db):
    """Yield an AsyncClient override for API endpoint tests."""

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user_token(db):
    """Generate user and access token."""
    from app.core.security import create_access_token
    from app.models.identity.user import User

    user = User(
        email=f"parser_test_{uuid.uuid4().hex}@example.com",
        password_hash="pass_hash",
        full_name="Parser Test User",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(subject=user.id)
    return token, user


def create_mock_completion_response(json_data: dict) -> MagicMock:
    """Create a mock LiteLLM completion response returning JSON."""
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = json.dumps(json_data)
    mock_choice.message = mock_message
    mock_resp.choices = [mock_choice]
    return mock_resp


# Successful JSON payload matching ParsedResumeResponse
VALID_PARSED_PAYLOAD = {
    "full_name": "Jane Developer",
    "summary": "Cloud Engineer with 4 years experience...",
    "education": [
        {
            "institution": "Stanford University",
            "degree": "BS",
            "field_of_study": "EE",
            "start_date": "2016-09-01",
            "end_date": "2020-06-01",
            "gpa": 3.9,
            "confidence": 0.95,
        }
    ],
    "work_experiences": [
        {
            "company": "SaaS Inc",
            "role": "Backend dev",
            "location": "Remote",
            "description": "Django APIs",
            "start_date": "2020-07-01",
            "end_date": None,
            "is_current": True,
            "confidence": 0.99,
        }
    ],
    "projects": [
        {
            "title": "Cloud Pipeline",
            "description": "CI/CD terraform project",
            "role": "Architect",
            "url": "https://github.com/jane/pipeline",
            "confidence": 0.94,
        }
    ],
    "skills": [{"name": "Terraform", "confidence": 1.0}],
    "certifications": ["AWS Cloud Practitioner"],
    "achievements": ["Dean's List 2019"],
    "confidence_score": 0.97,
    "parser_provider": "gemini",
    "parser_model": "gemini-2.5-flash",
    "parser_version": "1.0",
}


@pytest.mark.asyncio
async def test_factory_invalid_provider():
    # Force settings provider to unsupported string
    with patch.object(settings, "LLM_PROVIDER", "unsupported_llm"):
        with pytest.raises(ValueError) as exc:
            LLMFactory.create()
        assert "unsupported llm provider" in str(exc.value).lower()


@pytest.mark.asyncio
@patch("litellm.acompletion")
async def test_parser_service_success(mock_acompletion):
    mock_acompletion.return_value = create_mock_completion_response(
        VALID_PARSED_PAYLOAD
    )

    parser_service = ResumeParserService()
    parsed_obj = await parser_service.parse_resume("Jane Developer resume contents")

    assert isinstance(parsed_obj, ParsedResumeResponse)
    assert parsed_obj.full_name == "Jane Developer"
    assert parsed_obj.skills[0].name == "Terraform"
    assert parsed_obj.parser_provider == "gemini"


@pytest.mark.asyncio
@patch("litellm.acompletion")
async def test_parser_service_malformed_json(mock_acompletion):
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "this is not valid JSON string"
    mock_choice.message = mock_message
    mock_resp.choices = [mock_choice]
    mock_acompletion.return_value = mock_resp

    parser_service = ResumeParserService()
    with pytest.raises(InvalidAIResponseException) as exc:
        await parser_service.parse_resume("Resume content")
    assert "not valid JSON" in str(exc.value.detail)


@pytest.mark.asyncio
@patch("litellm.acompletion")
async def test_parser_service_missing_required_fields(mock_acompletion):
    # Missing required 'parser_provider' / 'parser_model' fields
    invalid_payload = VALID_PARSED_PAYLOAD.copy()
    invalid_payload.pop("parser_provider")

    mock_acompletion.return_value = create_mock_completion_response(invalid_payload)

    parser_service = ResumeParserService()
    with pytest.raises(InvalidAIResponseException) as exc:
        await parser_service.parse_resume("Resume content")
    assert "validation failed" in str(exc.value.detail)


@pytest.mark.asyncio
@patch("litellm.acompletion")
async def test_parser_service_connection_error(mock_acompletion):
    mock_acompletion.side_effect = litellm.exceptions.APIConnectionError(
        message="Cannot reach Gemini API",
        model=settings.LLM_MODEL,
        llm_provider="gemini",
    )

    parser_service = ResumeParserService()
    with pytest.raises(AIProviderUnavailableException) as exc:
        await parser_service.parse_resume("Resume content")
    assert "connect to gemini" in str(exc.value.detail).lower()


@pytest.mark.asyncio
@patch("litellm.acompletion")
async def test_parser_service_rate_limit_error(mock_acompletion):
    mock_acompletion.side_effect = litellm.exceptions.RateLimitError(
        message="Quota exceeded",
        model=settings.LLM_MODEL,
        llm_provider="gemini",
    )

    parser_service = ResumeParserService()
    with pytest.raises(AIProviderUnavailableException) as exc:
        await parser_service.parse_resume("Resume content")
    assert "rate limit exceeded" in str(exc.value.detail).lower()


@pytest.mark.asyncio
@patch("litellm.acompletion")
async def test_upload_api_success(mock_acompletion, client, test_user_token, db):
    token, _user = test_user_token
    headers = {"Authorization": f"Bearer {token}"}

    # Generate a valid PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Jane Developer resume content")
    pdf_bytes = doc.write()
    doc.close()

    mock_acompletion.return_value = create_mock_completion_response(
        VALID_PARSED_PAYLOAD
    )

    files = {
        "file": (
            "jane_cv.pdf",
            pdf_bytes,
            "application/pdf",
        )
    }

    response = await client.post("/api/v1/resume/upload", headers=headers, files=files)
    assert response.status_code == 201

    data = response.json()
    assert "resume_id" in data
    assert data["status"] == ResumeStatus.REVIEW_PENDING
    assert data["full_name"] == "Jane Developer"

    # Verify db record
    from sqlalchemy import select

    from app.models.resume.resume import Resume

    stmt = select(Resume).filter(Resume.id == data["resume_id"])
    resume_db = await db.scalar(stmt)
    assert resume_db is not None
    assert resume_db.status == ResumeStatus.REVIEW_PENDING
    assert resume_db.parsed_json is not None
    assert resume_db.parsed_json["full_name"] == "Jane Developer"

    # Clean up file
    if os.path.exists(resume_db.file_url):
        os.remove(resume_db.file_url)


@pytest.mark.asyncio
@patch("litellm.acompletion")
async def test_upload_api_parsing_failure(
    mock_acompletion, client, test_user_token, db
):
    token, user = test_user_token
    headers = {"Authorization": f"Bearer {token}"}

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Mock text contents")
    pdf_bytes = doc.write()
    doc.close()

    # Trigger complete failure in LLM completion
    mock_acompletion.side_effect = Exception("Internal model crash")

    files = {
        "file": (
            "jane_cv.pdf",
            pdf_bytes,
            "application/pdf",
        )
    }

    response = await client.post("/api/v1/resume/upload", headers=headers, files=files)
    assert response.status_code == 500
    assert "completion request failed" in response.json()["detail"].lower()

    # Verify that a FAILED Resume database record was still created
    from sqlalchemy import select

    from app.models.resume.resume import Resume

    stmt = select(Resume).filter(
        Resume.user_id == user.id, Resume.status == ResumeStatus.FAILED
    )
    resume_db = await db.scalar(stmt)
    assert resume_db is not None
    assert resume_db.status == ResumeStatus.FAILED
    assert resume_db.raw_text == "Mock text contents"

    # Clean up
    if os.path.exists(resume_db.file_url):
        os.remove(resume_db.file_url)

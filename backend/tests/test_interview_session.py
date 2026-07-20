import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.dependencies.providers import get_db
from app.main import app
from app.models.ai.candidate_profile import CandidateProfile
from app.models.interview.interview_blueprint import InterviewBlueprint
from app.models.interview.interview_session import InterviewSession
from app.models.resume.resume import Resume
from app.shared.enums import (
    DifficultyType,
    InterviewCategory,
    InterviewRole,
    ResumeStatus,
    SessionStatus,
)


def create_mock_completion_response(data: dict):
    class MockChoices:
        def __init__(self, content):
            self.message = MagicMock()
            self.message.content = content

    mock_resp = MagicMock()
    mock_resp.choices = [MockChoices(json.dumps(data))]
    return mock_resp


@pytest.fixture(autouse=True)
def mock_api_keys():
    """Autouse fixture to mock Gemini API keys."""
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
        email=f"session_test_{uuid.uuid4().hex}@example.com",
        password_hash="pass_hash",
        full_name="Session Test User",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(subject=user.id)
    return token, user


MOCK_BLUEPRINT_DATA = {
    "title": "Backend Technical Interview",
    "estimated_duration": 45,
    "sections": [
        {"name": "Introduction", "duration": 5},
        {"name": "Fundamentals", "duration": 20},
        {"name": "Coding Scenario", "duration": 15},
        {"name": "Wrap up", "duration": 5},
    ],
}


@pytest.mark.asyncio
async def test_interview_session_creation_success(client, db, test_user_token):
    """Test successful session creation, blueprint generation, and transition to READY status."""
    token, user = test_user_token

    # 1. Create a confirmed resume and a candidate profile
    resume = Resume(
        user_id=user.id,
        file_url="http://manual",
        original_filename="confirmed_resume.pdf",
        mime_type="application/pdf",
        file_size=1024,
        status=ResumeStatus.CONFIRMED,
        raw_text="Confirmed experience",
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    candidate_profile = CandidateProfile(
        resume_id=resume.id,
        user_id=user.id,
        profile_json={"summary": "Experienced Python Developer"},
    )
    db.add(candidate_profile)
    await db.commit()

    # Create mock response
    mock_litellm = create_mock_completion_response(MOCK_BLUEPRINT_DATA)

    payload = {
        "resume_id": str(resume.id),
        "category": "technical",
        "role": "backend",
    }

    with patch("litellm.acompletion", return_value=mock_litellm):
        headers = {"Authorization": f"Bearer {token}"}
        res = await client.post(
            "/api/v1/interview/session", json=payload, headers=headers
        )

        assert res.status_code == 201
        res_data = res.json()
        assert "session_id" in res_data
        assert res_data["status"] == "READY"
        assert res_data["blueprint_generated"] is True

        session_id = uuid.UUID(res_data["session_id"])

        # Assert DB session record
        stmt_s = select(InterviewSession).filter(InterviewSession.id == session_id)
        session_db = await db.scalar(stmt_s)
        assert session_db is not None
        assert session_db.user_id == user.id
        assert session_db.status == SessionStatus.READY
        assert session_db.interview_category == InterviewCategory.TECHNICAL
        assert session_db.role == InterviewRole.BACKEND
        assert session_db.difficulty == DifficultyType.ADAPTIVE
        assert session_db.duration_minutes == 45

        # Assert blueprint details
        stmt_b = select(InterviewBlueprint).filter(InterviewBlueprint.session_id == session_id)
        blueprint_db = await db.scalar(stmt_b)
        assert blueprint_db is not None
        assert blueprint_db.title == "Backend Technical Interview"
        assert blueprint_db.estimated_duration == 45
        assert blueprint_db.generated_by_profile == "interview_blueprint"
        # Since mocked profile is gemini-flash, resolved model should be gemini-2.5-flash
        assert blueprint_db.generated_model == "gemini/gemini-2.5-flash"
        assert len(blueprint_db.blueprint_json["sections"]) == 4


@pytest.mark.asyncio
async def test_interview_session_unconfirmed_resume(client, db, test_user_token):
    """Test that creating a session with a non-confirmed resume fails with a 400."""
    token, user = test_user_token

    resume = Resume(
        user_id=user.id,
        file_url="http://manual",
        original_filename="pending_resume.pdf",
        mime_type="application/pdf",
        file_size=1024,
        status=ResumeStatus.REVIEW_PENDING,
        raw_text="Pending review",
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    payload = {
        "resume_id": str(resume.id),
        "category": "coding",
    }

    headers = {"Authorization": f"Bearer {token}"}
    res = await client.post(
        "/api/v1/interview/session", json=payload, headers=headers
    )
    assert res.status_code == 400
    assert "confirmation required" in res.json()["detail"]


@pytest.mark.asyncio
async def test_interview_session_ownership_check(client, db, test_user_token):
    """Test that requesting session with a resume owned by another user fails with a 404."""
    token, _ = test_user_token

    from app.models.identity.user import User
    other_user = User(
        email="other_session_user@example.com",
        password_hash="pass_hash",
        full_name="Other User",
        is_active=True,
    )
    db.add(other_user)
    await db.commit()
    await db.refresh(other_user)

    resume = Resume(
        user_id=other_user.id,
        file_url="http://manual",
        original_filename="other.pdf",
        mime_type="application/pdf",
        file_size=1024,
        status=ResumeStatus.CONFIRMED,
        raw_text="Other content",
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    payload = {
        "resume_id": str(resume.id),
        "category": "coding",
    }

    headers = {"Authorization": f"Bearer {token}"}
    res = await client.post(
        "/api/v1/interview/session", json=payload, headers=headers
    )
    assert res.status_code == 404
    assert "Resume not found" in res.json()["detail"]


@pytest.mark.asyncio
async def test_interview_session_missing_technical_role(client, db, test_user_token):
    """Test that technical category session creation fails if role is missing."""
    token, user = test_user_token

    resume = Resume(
        user_id=user.id,
        file_url="http://manual",
        original_filename="resume.pdf",
        mime_type="application/pdf",
        file_size=1024,
        status=ResumeStatus.CONFIRMED,
        raw_text="Content",
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    candidate_profile = CandidateProfile(
        resume_id=resume.id,
        user_id=user.id,
        profile_json={"summary": "Experienced Python Developer"},
    )
    db.add(candidate_profile)
    await db.commit()

    payload = {
        "resume_id": str(resume.id),
        "category": "technical",
        # Missing role
    }

    headers = {"Authorization": f"Bearer {token}"}
    res = await client.post(
        "/api/v1/interview/session", json=payload, headers=headers
    )
    assert res.status_code == 400
    assert "Role is required for Technical interviews" in res.json()["detail"]


@pytest.mark.asyncio
async def test_interview_session_get_detail_unauthorized(client, db, test_user_token):
    """Test that retrieving session detail checks user ownership constraints."""
    token, _ = test_user_token

    from app.models.identity.user import User
    other_user = User(
        email="other_detail_user@example.com",
        password_hash="pass_hash",
        full_name="Other User",
        is_active=True,
    )
    db.add(other_user)
    await db.commit()
    await db.refresh(other_user)

    session = InterviewSession(
        user_id=other_user.id,
        interview_category=InterviewCategory.BEHAVIORAL,
        difficulty=DifficultyType.ADAPTIVE,
        duration_minutes=30,
        status=SessionStatus.READY,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    headers = {"Authorization": f"Bearer {token}"}
    res = await client.get(
        f"/api/v1/interview/session/{session.id}", headers=headers
    )
    assert res.status_code == 404
    assert "session not found" in res.json()["detail"].lower()

import uuid
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.dependencies.providers import get_db
from app.main import app
from app.models.ai.candidate_profile import CandidateProfile
from app.models.interview.interview_blueprint import InterviewBlueprint
from app.models.interview.interview_message import InterviewMessage
from app.models.interview.interview_session import InterviewSession
from app.models.resume.resume import Resume
from app.shared.enums import (
    DifficultyType,
    InterviewCategory,
    InterviewMessageRole,
    InterviewRole,
    InterviewState,
    ResumeStatus,
    SessionStatus,
)


def create_mock_completion_response(data: dict):
    from app.schemas.interview.interview_analysis import InterviewerTurnResponse, InterviewAnalysis
    from app.shared.enums import AnswerQuality
    
    msg = data.get("interviewer_message", "")
    analysis_data = data.get("analysis") or {
        "technical_accuracy": AnswerQuality.GOOD.value,
        "depth": AnswerQuality.GOOD.value,
        "coverage": AnswerQuality.GOOD.value,
        "communication": AnswerQuality.GOOD.value,
        "confidence": AnswerQuality.GOOD.value,
        "missing_topics": [],
        "strengths": [],
        "needs_followup": False,
    }
    analysis = InterviewAnalysis(**analysis_data)
    return InterviewerTurnResponse(analysis=analysis, interviewer_message=msg)


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
        email=f"conv_test_{uuid.uuid4().hex}@example.com",
        password_hash="pass_hash",
        full_name="Conversation Test User",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(subject=user.id)
    return token, user


@pytest_asyncio.fixture
async def another_user_token(db):
    """Generate another user and access token for unauthorized checks."""
    from app.core.security import create_access_token
    from app.models.identity.user import User

    user = User(
        email=f"conv_unauth_{uuid.uuid4().hex}@example.com",
        password_hash="pass_hash",
        full_name="Unauthorized Test User",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(subject=user.id)
    return token, user


@pytest_asyncio.fixture
async def active_session(db, test_user_token):
    """Setup a valid session in READY state with profile and blueprint populated."""
    _, user = test_user_token

    # 1. Create Resume
    resume = Resume(
        user_id=user.id,
        file_url="http://manual",
        original_filename="dummy.pdf",
        mime_type="application/pdf",
        file_size=1024,
        status=ResumeStatus.CONFIRMED,
    )
    db.add(resume)
    await db.flush()

    # 2. Create Candidate Profile
    profile = CandidateProfile(
        resume_id=resume.id,
        user_id=user.id,
        profile_json={"summary": "Highly motivated backend expert in python and databases."},
    )
    db.add(profile)
    await db.flush()

    # 3. Create Session
    session = InterviewSession(
        user_id=user.id,
        resume_id=resume.id,
        candidate_profile_id=profile.id,
        interview_category=InterviewCategory.TECHNICAL,
        role=InterviewRole.BACKEND,
        difficulty=DifficultyType.ADAPTIVE,
        duration_minutes=60,
        status=SessionStatus.READY,
        interview_state=InterviewState.READY.value,
        current_section_index=0,
    )
    db.add(session)
    await db.flush()

    # 4. Create Blueprint
    blueprint = InterviewBlueprint(
        session_id=session.id,
        title="Backend Engineering Core Blueprint",
        estimated_duration=60,
        blueprint_json={
            "title": "Backend Engineering Core Blueprint",
            "estimated_duration": 60,
            "sections": [
                {"name": "System Architecture", "duration": 30},
                {"name": "Database Internals & Indexes", "duration": 30},
            ],
        },
        generated_by_profile="interview_blueprint",
        generated_model="gemini",
    )
    db.add(blueprint)
    await db.commit()
    await db.refresh(session, ["blueprint", "candidate_profile"])
    return session


@pytest.mark.asyncio
async def test_start_interview_success(client, db, test_user_token, active_session):
    """Test successful start of interview session, generating AI greeting and saving state."""
    token, _ = test_user_token

    mock_llm_response = {"interviewer_message": "Hello Aditya! Welcome to the interview. Ready to start?"}

    with patch(
        "app.llm.orchestrator.LLMOrchestrator.structured_completion",
        return_value=create_mock_completion_response(mock_llm_response),
    ):
        res = await client.post(
            f"/api/v1/interview/session/{active_session.id}/start",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["message"] == "Hello Aditya! Welcome to the interview. Ready to start?"
        assert data["interview_state"] == "GREETING"
        assert data["session_status"] == "IN_PROGRESS"

        # Verify database session state
        stmt = select(InterviewSession).filter(InterviewSession.id == active_session.id)
        session_db = await db.scalar(stmt)
        assert session_db.status == SessionStatus.IN_PROGRESS
        assert session_db.interview_state == InterviewState.GREETING.value

        # Verify messages in db
        stmt_msg = select(InterviewMessage).filter(InterviewMessage.session_id == active_session.id)
        messages = (await db.scalars(stmt_msg)).all()
        assert len(messages) == 1
        assert messages[0].role == InterviewMessageRole.INTERVIEWER
        assert messages[0].sequence_number == 0


@pytest.mark.asyncio
async def test_start_interview_invalid_status(client, db, test_user_token, active_session):
    """Test that start is rejected if status is not READY."""
    token, _ = test_user_token

    # Change status to IN_PROGRESS
    active_session.status = SessionStatus.IN_PROGRESS
    await db.commit()

    res = await client.post(
        f"/api/v1/interview/session/{active_session.id}/start",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "Cannot start interview" in res.json()["detail"]


@pytest.mark.asyncio
async def test_start_interview_unauthorized(client, another_user_token, active_session):
    """Test that starting another user's session is unauthorized (404/Not Found)."""
    token, _ = another_user_token

    res = await client.post(
        f"/api/v1/interview/session/{active_session.id}/start",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_respond_flow_and_transitions(client, db, test_user_token, active_session):
    """Test complete flow: greeting -> candidate response -> introduction question."""
    token, _ = test_user_token

    # 1. Start the interview first
    with patch(
        "app.llm.orchestrator.LLMOrchestrator.structured_completion",
        return_value=create_mock_completion_response({"interviewer_message": "Greeting Question"}),
    ):
        await client.post(
            f"/api/v1/interview/session/{active_session.id}/start",
            headers={"Authorization": f"Bearer {token}"},
        )

    # 2. Respond to the greeting
    mock_intro_response = {"interviewer_message": "Tell me about your Python project."}

    with patch(
        "app.llm.orchestrator.LLMOrchestrator.structured_completion",
        return_value=create_mock_completion_response(mock_intro_response),
    ):
        res = await client.post(
            f"/api/v1/interview/session/{active_session.id}/respond",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "Yes, I am ready to start!"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["message"] == "Tell me about your Python project."
        assert data["interview_state"] == "INTRODUCTION"

        # Verify DB messages sequence numbers and roles
        stmt_msg = select(InterviewMessage).filter(
            InterviewMessage.session_id == active_session.id
        ).order_by(InterviewMessage.sequence_number.asc())
        messages = (await db.scalars(stmt_msg)).all()
        
        assert len(messages) == 3
        # Sequence 0: Interviewer greeting
        assert messages[0].role == InterviewMessageRole.INTERVIEWER
        assert messages[0].sequence_number == 0
        # Sequence 1: Candidate answer
        assert messages[1].role == InterviewMessageRole.CANDIDATE
        assert messages[1].sequence_number == 1
        assert messages[1].content == "Yes, I am ready to start!"
        # Sequence 2: Interviewer introduction
        assert messages[2].role == InterviewMessageRole.INTERVIEWER
        assert messages[2].sequence_number == 2


@pytest.mark.asyncio
async def test_respond_empty_message(client, test_user_token, active_session):
    """Test that empty messages are rejected with 400 Bad Request."""
    token, _ = test_user_token
    active_session.status = SessionStatus.IN_PROGRESS
    await client.post(
        f"/api/v1/interview/session/{active_session.id}/start",
        headers={"Authorization": f"Bearer {token}"},
    )

    res = await client.post(
        f"/api/v1/interview/session/{active_session.id}/respond",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "  "},
    )
    assert res.status_code == 400
    assert "cannot be empty" in res.json()["detail"]


@pytest.mark.asyncio
async def test_retrieve_messages_history(client, db, test_user_token, active_session):
    """Test retrieving chat history lists in order."""
    token, _ = test_user_token

    # Insert mock messages directly into db
    msg1 = InterviewMessage(session_id=active_session.id, role=InterviewMessageRole.INTERVIEWER, content="Q1", sequence_number=0)
    msg2 = InterviewMessage(session_id=active_session.id, role=InterviewMessageRole.CANDIDATE, content="A1", sequence_number=1)
    db.add_all([msg1, msg2])
    await db.commit()

    res = await client.get(
        f"/api/v1/interview/session/{active_session.id}/messages",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["content"] == "Q1"
    assert data[0]["role"] == "INTERVIEWER"
    assert data[1]["content"] == "A1"
    assert data[1]["role"] == "CANDIDATE"

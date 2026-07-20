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
from app.models.resume import Education, ResumeSkill, Skill, WorkExperience
from app.models.resume.resume import Resume
from app.shared.enums.resume import ResumeStatus


@pytest.fixture(autouse=True)
def mock_api_keys():
    """Autouse fixture to mock Gemini API keys."""
    with patch.object(settings, "GEMINI_API_KEY", "mock_key"), \
         patch.object(settings, "LITELLM_GEMINI_API_KEY", "mock_key"), \
         patch.object(settings, "LLM_FALLBACK_ORDER", ["gemini"]):
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
        email=f"confirm_test_{uuid.uuid4().hex}@example.com",
        password_hash="pass_hash",
        full_name="Confirm Test User",
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


# Mock Profile Response matching CandidateProfileResponse schema
MOCK_PROFILE_DATA = {
    "summary": "Experienced Python Developer",
    "estimated_experience_level": "Senior",
    "inferred_years_experience": 5.0,
    "recommended_interview_level": "L5/Senior",
    "primary_domain": "Backend",
    "secondary_domains": ["Cloud"],
    "detected_programming_languages": ["Python", "JavaScript"],
    "detected_technologies": ["REST", "Docker"],
    "frameworks": ["FastAPI", "Django"],
    "databases": ["PostgreSQL", "Redis"],
    "cloud_technologies": ["AWS"],
    "strengths_inferred_from_projects": ["Scalability"],
    "major_projects_summary": ["Project A"],
    "project_complexity": "High",
    "resume_presentation_summary": "Clean resume structure",
    "technology_confidence_scores": {"Python": 0.9},
    "overall_technical_profile": "Strong backend candidate",
}


@pytest.mark.asyncio
async def test_resume_confirmation_success(client, db, test_user_token):
    """Test successful resume confirmation, database normalization, and profile generation."""
    token, user = test_user_token

    # Create a draft resume
    resume = Resume(
        user_id=user.id,
        file_url="http://manual",
        original_filename="draft.json",
        mime_type="application/json",
        file_size=0,
        status=ResumeStatus.REVIEW_PENDING,
        raw_text="",
        parsed_json={"full_name": "Test User"},
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    resume_id = resume.id

    confirm_request = {
        "summary": "Experienced Engineer",
        "education": [
            {
                "institution": "Stanford University",
                "degree": "BS",
                "field_of_study": "Computer Science",
                "start_date": "2018-09-01",
                "end_date": "2022-06-01",
                "gpa": "3.8"
            }
        ],
        "work_experiences": [
            {
                "company": "FastAPI Tech",
                "role": "Software Engineer",
                "location": "Remote",
                "description": "Building cloud APIs",
                "start_date": "2022-07-01",
                "end_date": None,
                "is_current": True
            }
        ],
        "projects": [
            {
                "title": "Project X",
                "description": "Sleek FastAPI service",
                "role": "Lead",
                "url": "https://github.com/projectx"
            }
        ],
        "skills": [
            {"name": "Python", "confidence": 1.0},
            {"name": "Docker", "confidence": 0.9},
            {"name": "docker", "confidence": 0.8},
            {"name": " DOCKER", "confidence": 0.95}
        ],
        "certifications": ["AWS Solutions Architect"],
        "achievements": ["Hackathon Winner"]
    }

    mock_litellm = create_mock_completion_response(MOCK_PROFILE_DATA)

    with patch("litellm.acompletion", return_value=mock_litellm):
        headers = {"Authorization": f"Bearer {token}"}
        res = await client.post(
            f"/api/v1/resume/{resume_id}/confirm",
            json=confirm_request,
            headers=headers
        )

        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["resume_id"] == str(resume_id)

        # Fetch from database and assert updates
        stmt_res = select(Resume).filter(Resume.id == resume_id)
        resume_db = await db.scalar(stmt_res)
        assert resume_db.status == ResumeStatus.CONFIRMED
        assert resume_db.is_primary is True

        # Assert normalized relations
        stmt_edu = select(Education).filter(Education.resume_id == resume_id)
        edus = (await db.scalars(stmt_edu)).all()
        assert len(edus) == 1
        assert edus[0].institution == "Stanford University"

        stmt_exp = select(WorkExperience).filter(WorkExperience.resume_id == resume_id)
        exps = (await db.scalars(stmt_exp)).all()
        assert len(exps) == 1
        assert exps[0].company == "FastAPI Tech"

        # Assert skill deduplication & normalization (lowercase & trim)
        stmt_skills = select(ResumeSkill).filter(ResumeSkill.resume_id == resume_id)
        res_skills = (await db.scalars(stmt_skills)).all()
        assert len(res_skills) == 2  # "python" and "docker" (duplicates normalized to 'docker')

        stmt_docker = select(Skill).filter(Skill.name == "docker")
        dock_skills = (await db.scalars(stmt_docker)).all()
        assert len(dock_skills) == 1  # Exactly one unique Skill entry created

        # Assert Candidate Profile creation
        stmt_cp = select(CandidateProfile).filter(CandidateProfile.resume_id == resume_id)
        cp = await db.scalar(stmt_cp)
        assert cp is not None
        assert cp.user_id == user.id
        assert cp.profile_json["estimated_experience_level"] == "Senior"


@pytest.mark.asyncio
async def test_resume_confirmation_unauthorized(client, db, test_user_token):
    """Test that unauthorized users or users not owning the resume are rejected."""
    token, _user = test_user_token

    # Create another user in the database
    from app.models.identity.user import User
    another_user = User(
        email=f"other_user_{uuid.uuid4().hex}@example.com",
        password_hash="pass_hash",
        full_name="Other User",
        is_active=True,
    )
    db.add(another_user)
    await db.commit()
    await db.refresh(another_user)

    resume = Resume(
        user_id=another_user.id,
        file_url="http://manual",
        original_filename="other.json",
        mime_type="application/json",
        file_size=0,
        status=ResumeStatus.REVIEW_PENDING,
        raw_text="",
        parsed_json={"full_name": "Other User"},
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    resume_id = resume.id

    headers = {"Authorization": f"Bearer {token}"}
    res = await client.post(
        f"/api/v1/resume/{resume_id}/confirm",
        json={"skills": [{"name": "Python", "confidence": 1.0}]},
        headers=headers
    )
    assert res.status_code == 404  # Not found due to ownership check mismatch


@pytest.mark.asyncio
async def test_resume_confirmation_invalid_status(client, db, test_user_token):
    """Test that confirmation fails if resume status is not REVIEW_PENDING."""
    token, user = test_user_token

    # Create a resume with UPLOADED status (which should fail confirmation)
    resume = Resume(
        user_id=user.id,
        file_url="http://manual",
        original_filename="draft.json",
        mime_type="application/json",
        file_size=0,
        status=ResumeStatus.UPLOADED,
        raw_text="",
        parsed_json={"full_name": "Test User"},
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    resume_id = resume.id

    headers = {"Authorization": f"Bearer {token}"}
    res = await client.post(
        f"/api/v1/resume/{resume_id}/confirm",
        json={"skills": [{"name": "Python", "confidence": 1.0}]},
        headers=headers
    )
    assert res.status_code == 400
    assert "not allowed for status" in res.json()["detail"]


@pytest.mark.asyncio
async def test_resume_confirmation_idempotency(client, db, test_user_token):
    """Test confirmation idempotency: second request is rejected with 409 Conflict."""
    token, user = test_user_token

    # Create a confirmed resume
    resume = Resume(
        user_id=user.id,
        file_url="http://manual",
        original_filename="draft.json",
        mime_type="application/json",
        file_size=0,
        status=ResumeStatus.CONFIRMED,
        raw_text="",
        parsed_json={"full_name": "Test User"},
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    resume_id = resume.id

    headers = {"Authorization": f"Bearer {token}"}
    res = await client.post(
        f"/api/v1/resume/{resume_id}/confirm",
        json={"skills": [{"name": "Python", "confidence": 1.0}]},
        headers=headers
    )
    assert res.status_code == 409
    assert "already confirmed" in res.json()["detail"]


@pytest.mark.asyncio
async def test_resume_confirmation_rollback_on_ai_failure(client, db, test_user_token):
    """Test transactional rollback: if AI generation fails, no changes persist to database."""
    token, user = test_user_token

    # Create a draft resume
    resume = Resume(
        user_id=user.id,
        file_url="http://manual",
        original_filename="draft.json",
        mime_type="application/json",
        file_size=0,
        status=ResumeStatus.REVIEW_PENDING,
        raw_text="",
        parsed_json={"full_name": "Test User"},
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    resume_id = resume.id

    confirm_request = {
        "summary": "Experienced Engineer",
        "skills": [{"name": "Python", "confidence": 1.0}],
        "education": [
            {
                "institution": "Stanford University",
                "degree": "BS",
                "field_of_study": "Computer Science",
                "start_date": "2018-09-01",
                "end_date": "2022-06-01",
                "gpa": "3.8"
            }
        ]
    }

    # Force litellm mock to throw an exception
    with patch("litellm.acompletion", side_effect=Exception("API connection timeout")):
        headers = {"Authorization": f"Bearer {token}"}
        res = await client.post(
            f"/api/v1/resume/{resume_id}/confirm",
            json=confirm_request,
            headers=headers
        )

        assert res.status_code in (500, 503)

        # Assert no updates committed (atomicity verification)
        stmt_res = select(Resume).filter(Resume.id == resume_id)
        resume_db = await db.scalar(stmt_res)
        assert resume_db.status == ResumeStatus.REVIEW_PENDING  # Still pending review, not confirmed!
        assert resume_db.is_primary is False

        # Assert no normalized relations created (rolled back!)
        stmt_edu = select(Education).filter(Education.resume_id == resume_id)
        edus = (await db.scalars(stmt_edu)).all()
        assert len(edus) == 0

        # Assert no profile record created
        stmt_cp = select(CandidateProfile).filter(CandidateProfile.resume_id == resume_id)
        cp = await db.scalar(stmt_cp)
        assert cp is None

# ruff: noqa: F401
from app.db.base import Base
from app.models.ai.candidate_profile import CandidateProfile

# Import all models so Alembic can discover them.
from app.models.identity import User
from app.models.interview import (
    Company,
    Competency,
    InterviewBlueprint,
    InterviewCompetencyScore,
    InterviewEvent,
    InterviewMessage,
    InterviewQuestion,
    InterviewResponse,
    InterviewSession,
    InterviewTemplate,
    InterviewTurnAnalysis,
    QuestionBank,
    QuestionCompetency,
    QuestionTestCase,
    Role,
)
from app.models.resume import (
    Education,
    Project,
    ProjectSkill,
    Resume,
    ResumeSkill,
    Skill,
    SkillCategory,
    WorkExperience,
)

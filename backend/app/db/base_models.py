# ruff: noqa: F401
from app.db.base import Base

# Import all models so Alembic can discover them.
from app.models.identity import User
from app.models.interview import (
    Company,
    Competency,
    InterviewCompetencyScore,
    InterviewEvent,
    InterviewQuestion,
    InterviewResponse,
    InterviewSession,
    InterviewTemplate,
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

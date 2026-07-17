# ruff: noqa: F401, E402
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

# Import all models so Alembic can discover them.
from app.models.identity import User
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

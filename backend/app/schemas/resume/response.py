import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SkillCategoryResponse(BaseModel):
    """Schema for a technology competency category response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime


class SkillResponse(BaseModel):
    """Schema for a skill competency response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime


class EducationResponse(BaseModel):
    """Schema for academic credentials response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resume_id: uuid.UUID
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    gpa: float | None = None
    created_at: datetime
    updated_at: datetime


class WorkExperienceResponse(BaseModel):
    """Schema for professional work experience record response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resume_id: uuid.UUID
    company: str
    role: str
    location: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool
    created_at: datetime
    updated_at: datetime


class ProjectResponse(BaseModel):
    """Schema for project history record response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resume_id: uuid.UUID
    title: str
    description: str | None = None
    role: str | None = None
    url: HttpUrl | None = None
    created_at: datetime
    updated_at: datetime


class ResumeResponse(BaseModel):
    """Schema for a user's resume, complete with nested collections."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    file_url: HttpUrl
    raw_text: str | None = None
    parsed_json: dict | None = None
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    # Nested related domain models
    education: list[EducationResponse] = Field(default_factory=list)
    work_experiences: list[WorkExperienceResponse] = Field(default_factory=list)
    projects: list[ProjectResponse] = Field(default_factory=list)
    skills: list[SkillResponse] = Field(default_factory=list)

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.resume.request import (
    EducationCreateRequest,
    ProjectCreateRequest,
    WorkExperienceCreateRequest,
)
from app.shared.enums.resume import ResumeStatus


class UploadMetadata(BaseModel):
    """Strongly typed upload metadata model."""

    model_config = ConfigDict(from_attributes=True)

    file_url: str
    original_filename: str
    mime_type: str
    file_size: int


class ResumeUploadResponse(BaseModel):
    """Response containing uploaded resume metadata."""

    model_config = ConfigDict(from_attributes=True)

    resume_id: uuid.UUID
    status: ResumeStatus


class ParsedSkillResponse(BaseModel):
    """Schema for parsed technology competency from AI parser."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    confidence: float | None = None


class ParsedEducationResponse(BaseModel):
    """Schema for parsed education details from AI parser."""

    model_config = ConfigDict(from_attributes=True)

    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    gpa: float | None = None
    confidence: float | None = None


class ParsedWorkExperienceResponse(BaseModel):
    """Schema for parsed work experience details from AI parser."""

    model_config = ConfigDict(from_attributes=True)

    company: str
    role: str
    location: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    confidence: float | None = None


class ParsedProjectResponse(BaseModel):
    """Schema for parsed project details from AI parser."""

    model_config = ConfigDict(from_attributes=True)

    title: str
    description: str | None = None
    role: str | None = None
    url: HttpUrl | None = None
    confidence: float | None = None


class ParsedResumeResponse(BaseModel):
    """Temporary structured output returned by the AI parser before confirmation."""

    model_config = ConfigDict(from_attributes=True)

    full_name: str | None = None
    summary: str | None = None
    education: list[ParsedEducationResponse] = Field(default_factory=list)
    work_experiences: list[ParsedWorkExperienceResponse] = Field(
        default_factory=list
    )
    projects: list[ParsedProjectResponse] = Field(default_factory=list)
    skills: list[ParsedSkillResponse] = Field(default_factory=list)
    confidence_score: float | None = None


class ResumeConfirmationRequest(BaseModel):
    """Edited validation schemas confirmed by the candidate to persist resume data."""

    summary: str | None = None
    education: list[EducationCreateRequest] = Field(default_factory=list)
    work_experiences: list[WorkExperienceCreateRequest] = Field(
        default_factory=list
    )
    projects: list[ProjectCreateRequest] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)

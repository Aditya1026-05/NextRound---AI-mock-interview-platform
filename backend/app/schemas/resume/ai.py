import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    start_date: str | None = None
    end_date: str | None = None
    gpa: float | str | None = None
    confidence: float | None = None


class ParsedWorkExperienceResponse(BaseModel):
    """Schema for parsed work experience details from AI parser."""

    model_config = ConfigDict(from_attributes=True)

    company: str
    role: str
    location: str | None = None
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    confidence: float | None = None


class ParsedProjectResponse(BaseModel):
    """Schema for parsed project details from AI parser."""

    model_config = ConfigDict(from_attributes=True)

    title: str
    description: str | None = None
    role: str | None = None
    url: str | None = None
    confidence: float | None = None


class ParsedResumeResponse(BaseModel):
    """Temporary structured output returned by the AI parser before confirmation."""

    model_config = ConfigDict(from_attributes=True)

    resume_id: uuid.UUID | None = None
    status: ResumeStatus | None = None
    full_name: str | None = None
    summary: str | None = None
    education: list[ParsedEducationResponse] = Field(default_factory=list)
    work_experiences: list[ParsedWorkExperienceResponse] = Field(
        default_factory=list
    )
    projects: list[ParsedProjectResponse] = Field(default_factory=list)
    skills: list[ParsedSkillResponse] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    confidence_score: float | None = None
    parser_provider: str
    parser_model: str
    parser_version: str | None = None


class ResumeConfirmationRequest(BaseModel):
    """Edited validation schemas confirmed by the candidate to persist resume data."""

    summary: str | None = None
    education: list[EducationCreateRequest] = Field(default_factory=list)
    work_experiences: list[WorkExperienceCreateRequest] = Field(
        default_factory=list
    )
    projects: list[ProjectCreateRequest] = Field(default_factory=list)
    skills: list[ParsedSkillResponse] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


class ResumeListItem(BaseModel):
    """Schema representing basic resume metadata in a list view."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    status: ResumeStatus
    created_at: str
    is_primary: bool


class RenameResumeRequest(BaseModel):
    """Schema to rename a resume."""

    filename: str = Field(..., min_length=1, max_length=255)


class CandidateProfileResponse(BaseModel):
    """Schema representing AI-generated reusable candidate profile intelligence."""

    model_config = ConfigDict(from_attributes=True)

    summary: str
    estimated_experience_level: str
    inferred_years_experience: float
    recommended_interview_level: str
    primary_domain: str
    secondary_domains: list[str] = Field(default_factory=list)
    detected_programming_languages: list[str] = Field(default_factory=list)
    detected_technologies: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    cloud_technologies: list[str] = Field(default_factory=list)
    strengths_inferred_from_projects: list[str] = Field(default_factory=list)
    major_projects_summary: list[str] = Field(default_factory=list)
    project_complexity: str
    resume_presentation_summary: str
    technology_confidence_scores: dict[str, float] = Field(default_factory=dict)
    overall_technical_profile: str

    @field_validator(
        "secondary_domains",
        "detected_programming_languages",
        "detected_technologies",
        "frameworks",
        "databases",
        "cloud_technologies",
        "strengths_inferred_from_projects",
        "major_projects_summary",
        mode="before"
    )
    @classmethod
    def coerce_list_fields(cls, v):
        if isinstance(v, str):
            if "," in v:
                return [item.strip() for item in v.split(",") if item.strip()]
            return [v]
        return v


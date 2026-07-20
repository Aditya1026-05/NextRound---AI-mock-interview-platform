import uuid
from datetime import date

from pydantic import BaseModel, Field, HttpUrl


class ResumeCreateRequest(BaseModel):
    """Schema for creating a new resume."""

    file_url: HttpUrl = Field(..., description="The URL of the uploaded resume file")
    raw_text: str | None = Field(
        None, description="The raw parsed text content of the resume"
    )
    parsed_json: dict | None = Field(
        None, description="Structured metadata extracted from the resume"
    )
    is_primary: bool = Field(
        False, description="Whether this is the candidate's primary resume"
    )


class ResumeUpdateRequest(BaseModel):
    """Schema for updating an existing resume."""

    file_url: HttpUrl | None = Field(
        None, description="The URL of the uploaded resume file"
    )
    raw_text: str | None = Field(
        None, description="The raw parsed text content of the resume"
    )
    parsed_json: dict | None = Field(
        None, description="Structured metadata extracted from the resume"
    )
    is_primary: bool | None = Field(
        None, description="Whether this is the candidate's primary resume"
    )


class EducationCreateRequest(BaseModel):
    """Schema for creating a new education history record."""

    institution: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the academic institution",
    )
    degree: str | None = Field(
        None, max_length=255, description="Academic degree obtained"
    )
    field_of_study: str | None = Field(
        None, max_length=255, description="Major or field of study"
    )
    start_date: date | None = Field(None, description="Start date of the education")
    end_date: date | None = Field(
        None, description="Graduation or end date of the education"
    )
    gpa: float | None = Field(None, description="Grade point average")


class EducationUpdateRequest(BaseModel):
    """Schema for updating an existing education history record."""

    institution: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="Name of the academic institution",
    )
    degree: str | None = Field(
        None, max_length=255, description="Academic degree obtained"
    )
    field_of_study: str | None = Field(
        None, max_length=255, description="Major or field of study"
    )
    start_date: date | None = Field(None, description="Start date of the education")
    end_date: date | None = Field(
        None, description="Graduation or end date of the education"
    )
    gpa: float | None = Field(None, description="Grade point average")


class WorkExperienceCreateRequest(BaseModel):
    """Schema for creating a new work experience record."""

    company: str = Field(
        ..., min_length=1, max_length=255, description="Name of the employer company"
    )
    role: str = Field(
        ..., min_length=1, max_length=255, description="Job title or role"
    )
    location: str | None = Field(
        None, max_length=255, description="Office location or remote"
    )
    description: str | None = Field(None, description="Job details and achievements")
    start_date: date | None = Field(None, description="Employment start date")
    end_date: date | None = Field(None, description="Employment end date")
    is_current: bool = Field(
        False, description="Whether this is the candidate's current job"
    )


class WorkExperienceUpdateRequest(BaseModel):
    """Schema for updating an existing work experience record."""

    company: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="Name of the employer company",
    )
    role: str | None = Field(
        None, min_length=1, max_length=255, description="Job title or role"
    )
    location: str | None = Field(
        None, max_length=255, description="Office location or remote"
    )
    description: str | None = Field(None, description="Job details and achievements")
    start_date: date | None = Field(None, description="Employment start date")
    end_date: date | None = Field(None, description="Employment end date")
    is_current: bool | None = Field(
        None, description="Whether this is the candidate's current job"
    )


class ProjectCreateRequest(BaseModel):
    """Schema for creating a new project history record."""

    title: str = Field(
        ..., min_length=1, max_length=255, description="Title of the project"
    )
    description: str | None = Field(
        None, description="Description of the project goals and architecture"
    )
    role: str | None = Field(
        None, max_length=255, description="Candidate's role in the project"
    )
    url: HttpUrl | None = Field(
        None, description="Optional URL to the hosted project or repository"
    )


class ProjectUpdateRequest(BaseModel):
    """Schema for updating an existing project history record."""

    title: str | None = Field(
        None, min_length=1, max_length=255, description="Title of the project"
    )
    description: str | None = Field(
        None, description="Description of the project goals and architecture"
    )
    role: str | None = Field(
        None, max_length=255, description="Candidate's role in the project"
    )
    url: HttpUrl | None = Field(
        None, description="Optional URL to the hosted project or repository"
    )


class SkillCategoryCreateRequest(BaseModel):
    """Schema for creating a technology competency category."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the skill category",
    )


class SkillCreateRequest(BaseModel):
    """Schema for creating a new skill competency."""

    category_id: uuid.UUID = Field(
        ..., description="The ID of the parent category this skill belongs to"
    )
    name: str = Field(
        ..., min_length=1, max_length=100, description="Name of the skill"
    )

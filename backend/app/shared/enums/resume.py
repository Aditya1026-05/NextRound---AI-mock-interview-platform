from enum import StrEnum


class ResumeStatus(StrEnum):
    """Status indicating the parsing phase of a candidate's resume."""

    UPLOADED = "uploaded"
    PARSING = "parsing"
    REVIEW_PENDING = "review_pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"

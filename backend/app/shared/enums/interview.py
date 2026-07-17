from enum import StrEnum


class DifficultyType(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class InterviewType(StrEnum):
    CODING = "coding"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system-design"
    ML = "ml"
    HYBRID = "hybrid"


class SessionStatus(StrEnum):
    IDLE = "idle"
    IN_PROGRESS = "in_progress"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"


class EndedReasonType(StrEnum):
    COMPLETED = "completed"
    USER_LEFT = "user_left"
    TIMEOUT = "timeout"
    NETWORK_FAILURE = "network_failure"
    SYSTEM_FAILURE = "system_failure"
    TERMINATED = "terminated"


class ResponseType(StrEnum):
    VOICE = "voice"
    TEXT = "text"
    CODE = "code"

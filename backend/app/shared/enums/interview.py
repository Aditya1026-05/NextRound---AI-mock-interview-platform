from enum import StrEnum


class DifficultyType(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ADAPTIVE = "adaptive"


class InterviewCategory(StrEnum):
    TECHNICAL = "technical"
    CODING = "coding"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system_design"


class InterviewRole(StrEnum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    FULLSTACK = "fullstack"
    AI_ML = "ai_ml"
    DATA_SCIENCE = "data_science"
    DEVOPS = "devops"
    MOBILE = "mobile"


class InterviewType(StrEnum):
    CODING = "coding"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system-design"
    ML = "ml"
    HYBRID = "hybrid"


class SessionStatus(StrEnum):
    CREATED = "CREATED"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


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


class InterviewState(StrEnum):
    READY = "READY"
    GREETING = "GREETING"
    INTRODUCTION = "INTRODUCTION"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSING = "CLOSING"
    COMPLETED = "COMPLETED"


class InterviewMessageRole(StrEnum):
    SYSTEM = "SYSTEM"
    INTERVIEWER = "INTERVIEWER"
    CANDIDATE = "CANDIDATE"


class InterviewAction(StrEnum):
    FOLLOW_UP = "FOLLOW_UP"
    CLARIFY = "CLARIFY"
    NEXT_QUESTION = "NEXT_QUESTION"
    INCREASE_DIFFICULTY = "INCREASE_DIFFICULTY"
    DECREASE_DIFFICULTY = "DECREASE_DIFFICULTY"
    CHANGE_TOPIC = "CHANGE_TOPIC"
    SECTION_COMPLETE = "SECTION_COMPLETE"


class AnswerQuality(StrEnum):
    POOR = "POOR"
    FAIR = "FAIR"
    GOOD = "GOOD"
    EXCELLENT = "EXCELLENT"
    NOT_APPLICABLE = "N/A"


class DifficultyLevel(StrEnum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class QuestionType(StrEnum):
    PRIMARY = "PRIMARY"
    FOLLOW_UP = "FOLLOW_UP"
    CLARIFICATION = "CLARIFICATION"
    TRANSITION = "TRANSITION"
    INTRODUCTION = "INTRODUCTION"
    CLOSING = "CLOSING"


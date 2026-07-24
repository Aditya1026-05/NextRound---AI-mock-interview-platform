import uuid
from pydantic import BaseModel
from app.shared.enums import HintLevel

class FollowUpQuestion(BaseModel):
    question: str
    purpose: str
    expected_answer: str

class CodingHint(BaseModel):
    level: HintLevel
    content: str
    purpose: str

class CodingProblemResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    difficulty: str
    function_signatures: dict[str, str]
    optimal_solutions: dict[str, str]
    optimal_time_complexity: str
    optimal_space_complexity: str
    hints: list[CodingHint]
    follow_ups: list[FollowUpQuestion]
    estimated_duration_minutes: int | None = None
    recommended_languages: list[str] | None = None
    learning_objectives: list[str] | None = None
    topics: list[str] = []
    companies: list[str] = []

    class Config:
        from_attributes = True

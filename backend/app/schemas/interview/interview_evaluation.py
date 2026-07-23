import uuid
from typing import Any
from pydantic import BaseModel


class QuestionReviewItemSchema(BaseModel):
    """Pydantic schema representing a single question review in the timeline."""

    question_id: uuid.UUID
    question_number: int
    score: int
    ideal_answer: str
    evaluation: str
    strengths: list[str]
    improvements: list[str]


class TimelineReviewResponseSchema(BaseModel):
    """Joined question/answer pair detail response for frontend timeline rendering."""

    question: str
    answer: str
    score: int
    ideal_answer: str
    evaluation: str
    strengths: list[str]
    improvements: list[str]


class InterviewEvaluationResponseSchema(BaseModel):
    """Pydantic schema representing the complete response for interview evaluation."""

    id: uuid.UUID
    session_id: uuid.UUID
    overall_score: int
    recommendation: str
    summary: str | None
    skill_scores: dict[str, float]
    timeline_reviews: list[TimelineReviewResponseSchema]
    evaluation_version: str

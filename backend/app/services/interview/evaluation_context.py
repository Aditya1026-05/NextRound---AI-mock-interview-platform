from typing import Any
from pydantic import BaseModel


class EvaluationContext(BaseModel):
    """Immutable evaluation context passed to the EvaluationPromptBuilder."""

    session_id: str
    interview_category: str
    overall_score: int
    recommendation: str
    skill_scores: dict[str, float]
    transcript: list[dict[str, Any]]
    turn_analyses: list[dict[str, Any]]

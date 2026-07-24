from typing import Any
from pydantic import BaseModel

from app.shared.enums import DiscussionPhase, HintLevel
from app.schemas.interview.coding_problem import CodingProblemResponse

class CodingContext(BaseModel):
    """Context object representing the current state of a coding interview section."""

    active_problem: CodingProblemResponse
    discussion_phase: DiscussionPhase
    current_hint_level: HintLevel
    language: str
    transcript: list[dict[str, Any]]
    blueprint: dict[str, Any] | None = None

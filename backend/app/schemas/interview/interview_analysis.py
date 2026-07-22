from pydantic import BaseModel

from app.shared.enums import AnswerQuality


class InterviewAnalysis(BaseModel):
    """Pydantic model representing structured observational analysis of candidate's latest response."""

    technical_accuracy: AnswerQuality
    depth: AnswerQuality
    coverage: AnswerQuality
    communication: AnswerQuality
    confidence: AnswerQuality
    missing_topics: list[str]
    strengths: list[str]
    needs_followup: bool
    should_transition_topic: bool
    should_transition_section: bool


class InterviewerTurnResponse(BaseModel):
    """Root structured response model returned by LiteLLM containing observations and next message."""

    analysis: InterviewAnalysis
    interviewer_message: str

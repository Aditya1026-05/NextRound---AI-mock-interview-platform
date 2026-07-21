import structlog
from pydantic import BaseModel

from app.llm.orchestrator import LLMOrchestrator
from app.services.interview.prompt_builder import PromptContext

logger = structlog.get_logger()


class InterviewerResponseSchema(BaseModel):
    """Schema representing the raw response from the interviewer LLM Agent."""
    interviewer_message: str


class InterviewerAgent:
    """Invokes structured completion completions using LLMOrchestrator for the interview conversation profile."""

    def __init__(self):
        self.orchestrator = LLMOrchestrator()

    async def generate_response(self, context: PromptContext) -> str:
        """Call LLM orchestrator using logical profile 'interview_conversation' to generate next response."""
        result: InterviewerResponseSchema = await self.orchestrator.structured_completion(
            profile="interview_conversation",
            system_prompt=context.system_prompt,
            user_prompt=context.user_prompt,
            response_model=InterviewerResponseSchema,
        )
        return result.interviewer_message.strip()

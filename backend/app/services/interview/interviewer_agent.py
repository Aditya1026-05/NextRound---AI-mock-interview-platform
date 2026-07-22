import structlog

from app.llm.orchestrator import LLMOrchestrator
from app.schemas.interview.interview_analysis import InterviewerTurnResponse
from app.services.interview.prompt_builder import PromptContext

logger = structlog.get_logger()


class InterviewerAgent:
    """Invokes structured completions using LLMOrchestrator for the interview conversation profile."""

    def __init__(self):
        self.orchestrator = LLMOrchestrator()

    async def generate_response(self, context: PromptContext) -> InterviewerTurnResponse:
        """Call LLM orchestrator using logical profile 'interview_conversation' to generate structured response."""
        result: InterviewerTurnResponse = await self.orchestrator.structured_completion(
            profile="interview_conversation",
            system_prompt=context.system_prompt,
            user_prompt=context.user_prompt,
            response_model=InterviewerTurnResponse,
        )
        return result

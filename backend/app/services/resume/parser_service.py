from app.core.config import settings
from app.core.observability import log_operation
from app.llm.orchestrator import LLMOrchestrator
from app.prompts.resume import RESUME_PARSER_SYSTEM_PROMPT
from app.schemas.resume.ai import ParsedResumeResponse


class ResumeParserService:
    """Orchestrator service for parsing resume raw text using active LLM provider."""

    def __init__(self):
        self.orchestrator = LLMOrchestrator()

    @log_operation(category="SERVICE", name="Resume Parsing")
    async def parse_resume(self, raw_text: str) -> ParsedResumeResponse:
        """Call structured completion through provider and return parsed model."""
        parsed_obj = await self.orchestrator.structured_completion(
            profile="resume_parser",
            system_prompt=RESUME_PARSER_SYSTEM_PROMPT,
            user_prompt=raw_text,
            response_model=ParsedResumeResponse,
        )

        # Set or override provider analytics metadata
        parsed_obj.parser_provider = settings.LLM_PROVIDER
        parsed_obj.parser_model = settings.LLM_MODEL
        parsed_obj.parser_version = "1.0"

        return parsed_obj

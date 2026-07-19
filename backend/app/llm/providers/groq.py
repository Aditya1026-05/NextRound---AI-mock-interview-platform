from pydantic import BaseModel

from app.llm.base import LLMProvider


class GroqProvider(LLMProvider):
    """Placeholder provider structure for Groq API."""

    async def structured_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        raise NotImplementedError("Groq LLM provider is not yet implemented")

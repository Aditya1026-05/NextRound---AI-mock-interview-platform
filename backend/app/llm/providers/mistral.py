from pydantic import BaseModel

from app.llm.base import LLMProvider


class MistralProvider(LLMProvider):
    """Placeholder provider structure for Mistral API."""

    async def structured_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        raise NotImplementedError("Mistral LLM provider is not yet implemented")

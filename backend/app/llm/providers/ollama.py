from pydantic import BaseModel

from app.llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    """Placeholder provider structure for Ollama local API."""

    async def structured_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        model_name: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
    ) -> BaseModel:
        raise NotImplementedError("Ollama LLM provider is not yet implemented")

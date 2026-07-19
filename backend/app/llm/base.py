from abc import ABC, abstractmethod

from pydantic import BaseModel


class LLMProvider(ABC):
    """Abstract interface defining standard LLM provider behaviors."""

    @abstractmethod
    async def structured_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        """Call LLM and parse output into a validated Pydantic model."""
        pass

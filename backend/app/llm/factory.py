from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.providers.gemini import GeminiProvider
from app.llm.providers.groq import GroqProvider
from app.llm.providers.mistral import MistralProvider
from app.llm.providers.ollama import OllamaProvider


class LLMFactory:
    """Factory responsible for instantiating LLM providers."""

    @staticmethod
    def create() -> LLMProvider:
        """Resolve settings LLM provider and return configured instance."""
        return LLMFactory.create_by_name(settings.LLM_PROVIDER)

    @staticmethod
    def create_by_name(provider_name: str) -> LLMProvider:
        """Instantiate and return specified LLM provider by name."""
        provider_name = provider_name.lower().strip()

        if provider_name == "gemini":
            return GeminiProvider()
        elif provider_name == "groq":
            return GroqProvider()
        elif provider_name == "mistral":
            return MistralProvider()
        elif provider_name == "ollama":
            return OllamaProvider()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")

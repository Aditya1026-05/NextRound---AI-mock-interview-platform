from typing import Dict, Type
from app.services.interview.code_execution_provider import CodeExecutionProvider


class CodeExecutionProviderFactory:
    """Registry-based factory resolving concrete code execution engines."""

    _registry: Dict[str, Type[CodeExecutionProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: Type[CodeExecutionProvider]) -> None:
        """Register a new execution provider to the factory registry."""
        cls._registry[name.lower()] = provider_cls

    @classmethod
    def get_provider(cls, name: str) -> CodeExecutionProvider:
        """Instantiates and returns the configured execution provider."""
        if not cls._registry:
            from app.services.interview.judge0_code_execution_provider import Judge0CodeExecutionProvider
        provider_key = name.lower()
        if provider_key not in cls._registry:
            raise ValueError(
                f"Execution provider '{name}' is not registered. "
                f"Available providers: {list(cls._registry.keys())}"
            )
        provider_cls = cls._registry[provider_key]
        return provider_cls()

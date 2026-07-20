import os

import yaml
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings


class ModelCapabilities(BaseModel):
    """Pydantic schema representing the specific capabilities of an LLM model."""

    supports_streaming: bool = True
    supports_json: bool = True
    supports_function_calling: bool = True
    max_context_tokens: int = 4096


class ModelRegistryConfig(BaseModel):
    """Pydantic schema representing configuration for a model in the registry."""

    provider: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 2048
    timeout: int = 30
    capabilities: ModelCapabilities = Field(default_factory=ModelCapabilities)


class ProfileConfig(BaseModel):
    """Pydantic schema representing configuration for a logical LLM workload profile."""

    primary: str
    fallbacks: list[str] = Field(default_factory=list)
    retries: int = 0
    retry_delay: float = 0.0


class CompletionOverrides(BaseModel):
    """Type-safe Pydantic model for dynamic per-call parameter overrides."""

    temperature: float | None = None
    max_tokens: int | None = None
    timeout: int | None = None


class LLMRegistry:
    """Registry responsible for loading, validating, and exposing LLM models and profiles configuration."""

    def __init__(self, profiles_path: str | None = None):
        self.profiles_path = profiles_path or settings.LLM_PROFILES_PATH
        self.models: dict[str, ModelRegistryConfig] = {}
        self.profiles: dict[str, ProfileConfig] = {}
        self.load_and_validate()

    def load_and_validate(self) -> None:
        """Load YAML configuration from file and run full schema & cross-reference validations."""
        if not os.path.exists(self.profiles_path):
            raise FileNotFoundError(
                f"LLM Profiles configuration file not found at: {self.profiles_path}"
            )

        try:
            with open(self.profiles_path, encoding="utf-8") as f:
                raw_config = yaml.safe_load(f) or {}
        except Exception as e:
            raise ValueError(f"Failed to read/parse YAML profiles file: {e}") from e

        # Validate structure existence
        if "models" not in raw_config:
            raise ValueError(
                "Configuration file missing required top-level 'models' registry"
            )
        if "profiles" not in raw_config:
            raise ValueError(
                "Configuration file missing required top-level 'profiles' configuration"
            )

        # Parse Models
        models_dict = raw_config["models"]
        for key, val in models_dict.items():
            try:
                self.models[key] = ModelRegistryConfig.model_validate(val)
            except ValidationError as e:
                raise ValueError(
                    f"Invalid model configuration in registry for '{key}': {e}"
                ) from e

        # Parse Profiles
        profiles_dict = raw_config["profiles"]
        for key, val in profiles_dict.items():
            try:
                self.profiles[key] = ProfileConfig.model_validate(val)
            except ValidationError as e:
                raise ValueError(
                    f"Invalid profile configuration for '{key}': {e}"
                ) from e

        # Validate Cross-references (Fail-fast Startup Check)
        for name, profile in self.profiles.items():
            if profile.primary not in self.models:
                raise ValueError(
                    f"Validation error in profile '{name}': "
                    f"primary model '{profile.primary}' is not registered in 'models'"
                )
            for fallback in profile.fallbacks:
                if fallback not in self.models:
                    raise ValueError(
                        f"Validation error in profile '{name}': "
                        f"fallback model '{fallback}' is not registered in 'models'"
                    )

    def get_model(self, name: str) -> ModelRegistryConfig:
        """Retrieve model configuration by registry alias name."""
        if name not in self.models:
            raise KeyError(
                f"Requested model '{name}' is not registered in the Model Registry"
            )
        return self.models[name]

    def get_profile(self, name: str) -> ProfileConfig:
        """Retrieve Logical Profile configuration by profile key name."""
        if name not in self.profiles:
            raise KeyError(f"Requested LLM Profile '{name}' is not defined")
        return self.profiles[name]

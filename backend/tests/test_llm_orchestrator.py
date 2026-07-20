import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import litellm
import pytest
from pydantic import BaseModel, ValidationError

from app.core.exceptions import (
    InvalidAIResponseException,
)
from app.llm.orchestrator import LLMOrchestrator, _is_transient_error
from app.llm.registry import CompletionOverrides, LLMRegistry


class MockResponseModel(BaseModel):
    name: str


# Valid YAML configuration sample for testing
VALID_YAML = """
models:
  gemini-flash:
    provider: "gemini"
    model: "gemini/gemini-2.5-flash"
    temperature: 0.0
    max_tokens: 4096
    timeout: 30
    capabilities:
      supports_streaming: true
      supports_json: true
      supports_function_calling: true
      max_context_tokens: 1048576

  groq-llama:
    provider: "groq"
    model: "groq/llama-3.1-70b-versatile"
    temperature: 0.2
    max_tokens: 2048
    timeout: 15
    capabilities:
      supports_streaming: true
      supports_json: true
      supports_function_calling: true
      max_context_tokens: 131072

profiles:
  resume_parser:
    primary: "gemini-flash"
    fallbacks: ["groq-llama"]
    retries: 2
    retry_delay: 0.1
"""

# Invalid YAML configuration sample (references non-existent fallback model)
INVALID_YAML = """
models:
  gemini-flash:
    provider: "gemini"
    model: "gemini/gemini-2.5-flash"

profiles:
  resume_parser:
    primary: "gemini-flash"
    fallbacks: ["non-existent-model"]
"""


@pytest.fixture
def temp_llm_yaml():
    """Create a temporary valid YAML config file."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w") as f:
        f.write(VALID_YAML)
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def temp_invalid_yaml():
    """Create a temporary invalid YAML config file."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w") as f:
        f.write(INVALID_YAML)
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_is_transient_error_detection():
    """Verify that transient network errors are correctly detected while validation/auth errors are not."""
    e_503 = Exception(
        "VertexAIException - 503 unavailable Spikes in demand are temporary"
    )
    assert _is_transient_error(e_503) is True

    e_conn = litellm.exceptions.APIConnectionError(
        "connection failure timeout", model="gemini", llm_provider="gemini"
    )
    assert _is_transient_error(e_conn) is True

    e_val = InvalidAIResponseException(
        "Pydantic model validation failed: name required"
    )
    assert _is_transient_error(e_val) is False

    e_auth = litellm.exceptions.AuthenticationError(
        "Authentication key is invalid", model="gemini", llm_provider="gemini"
    )
    assert _is_transient_error(e_auth) is False


def test_registry_loading_and_getters(temp_llm_yaml):
    """Verify registry loads models and profiles correctly and checks capabilities."""
    registry = LLMRegistry(profiles_path=temp_llm_yaml)

    # Assert model loaded
    model = registry.get_model("gemini-flash")
    assert model.provider == "gemini"
    assert model.model == "gemini/gemini-2.5-flash"
    assert model.capabilities.supports_json is True
    assert model.capabilities.max_context_tokens == 1048576

    # Assert profile loaded
    profile = registry.get_profile("resume_parser")
    assert profile.primary == "gemini-flash"
    assert profile.fallbacks == ["groq-llama"]
    assert profile.retries == 2
    assert profile.retry_delay == 0.1

    # Assert raises KeyError for invalid getters
    with pytest.raises(KeyError):
        registry.get_model("unknown-model")
    with pytest.raises(KeyError):
        registry.get_profile("unknown-profile")


def test_registry_validation_fail_fast(temp_invalid_yaml):
    """Verify fail-fast startup checks raise ValueErrors on invalid YAML configuration schemas."""
    with pytest.raises(ValueError) as exc_info:
        LLMRegistry(profiles_path=temp_invalid_yaml)
    assert "is not registered in 'models'" in str(exc_info.value)


def test_completion_overrides_validation():
    """Verify type-safety validations on CompletionOverrides model."""
    overrides = CompletionOverrides(temperature=0.7, max_tokens=100)
    assert overrides.temperature == 0.7
    assert overrides.max_tokens == 100
    assert overrides.timeout is None

    # Invalid types raise validation errors
    with pytest.raises(ValidationError):
        CompletionOverrides(temperature="invalid_str")


@pytest.mark.asyncio
@patch("app.llm.factory.LLMFactory.create_by_name")
async def test_orchestrator_success_first_try(mock_create_by_name, temp_llm_yaml):
    """Verify orchestrator runs primary provider with parameters successfully."""
    registry = LLMRegistry(profiles_path=temp_llm_yaml)
    mock_gemini = MagicMock()
    mock_gemini.structured_completion = AsyncMock(
        return_value=MockResponseModel(name="Success Output")
    )
    mock_create_by_name.return_value = mock_gemini

    orchestrator = LLMOrchestrator(registry=registry)
    res = await orchestrator.structured_completion(
        profile="resume_parser",
        system_prompt="sys",
        user_prompt="usr",
        response_model=MockResponseModel,
    )

    assert res.name == "Success Output"
    mock_create_by_name.assert_called_once_with("gemini")
    mock_gemini.structured_completion.assert_called_once_with(
        system_prompt="sys",
        user_prompt="usr",
        response_model=MockResponseModel,
        model_name="gemini/gemini-2.5-flash",
        temperature=0.0,
        max_tokens=4096,
        timeout=30,
    )


@pytest.mark.asyncio
@patch("app.llm.factory.LLMFactory.create_by_name")
async def test_orchestrator_overrides_applied(mock_create_by_name, temp_llm_yaml):
    """Verify that per-call overrides are applied and override registry default variables."""
    registry = LLMRegistry(profiles_path=temp_llm_yaml)
    mock_gemini = MagicMock()
    mock_gemini.structured_completion = AsyncMock(
        return_value=MockResponseModel(name="Overrides Output")
    )
    mock_create_by_name.return_value = mock_gemini

    orchestrator = LLMOrchestrator(registry=registry)
    overrides = CompletionOverrides(temperature=0.9, max_tokens=500, timeout=10)
    res = await orchestrator.structured_completion(
        profile="resume_parser",
        system_prompt="sys",
        user_prompt="usr",
        response_model=MockResponseModel,
        overrides=overrides,
    )

    assert res.name == "Overrides Output"
    mock_gemini.structured_completion.assert_called_once_with(
        system_prompt="sys",
        user_prompt="usr",
        response_model=MockResponseModel,
        model_name="gemini/gemini-2.5-flash",
        temperature=0.9,
        max_tokens=500,
        timeout=10,
    )


@pytest.mark.asyncio
@patch("app.llm.factory.LLMFactory.create_by_name")
async def test_orchestrator_retries_and_fallback(mock_create_by_name, temp_llm_yaml):
    """Verify that transient errors trigger retries, and fallback to next provider is executed when retries exceed."""
    registry = LLMRegistry(profiles_path=temp_llm_yaml)

    mock_gemini = MagicMock()
    # Fails with transient connection error
    mock_gemini.structured_completion = AsyncMock(
        side_effect=Exception("VertexAI 503 temporary unavailable")
    )

    mock_groq = MagicMock()
    mock_groq.structured_completion = AsyncMock(
        return_value=MockResponseModel(name="Groq fallback output")
    )

    def factory_mock(name):
        if name == "gemini":
            return mock_gemini
        elif name == "groq":
            return mock_groq
        return None

    mock_create_by_name.side_effect = factory_mock

    orchestrator = LLMOrchestrator(registry=registry)
    res = await orchestrator.structured_completion(
        profile="resume_parser",
        system_prompt="sys",
        user_prompt="usr",
        response_model=MockResponseModel,
    )

    assert res.name == "Groq fallback output"
    # Should attempt gemini 3 times (1 initial + 2 retries)
    assert mock_gemini.structured_completion.call_count == 3
    # Groq should run once
    assert mock_groq.structured_completion.call_count == 1


@pytest.mark.asyncio
@patch("app.llm.factory.LLMFactory.create_by_name")
async def test_orchestrator_non_transient_fails_immediately(
    mock_create_by_name, temp_llm_yaml
):
    """Verify that non-transient validation exceptions fail fast immediately without retry or fallback."""
    registry = LLMRegistry(profiles_path=temp_llm_yaml)

    mock_gemini = MagicMock()
    # Raise non-transient Pydantic validation / InvalidAIResponseException
    mock_gemini.structured_completion = AsyncMock(
        side_effect=InvalidAIResponseException("Pydantic validation failed")
    )

    mock_groq = MagicMock()
    mock_create_by_name.return_value = mock_gemini

    orchestrator = LLMOrchestrator(registry=registry)
    with pytest.raises(InvalidAIResponseException):
        await orchestrator.structured_completion(
            profile="resume_parser",
            system_prompt="sys",
            user_prompt="usr",
            response_model=MockResponseModel,
        )

    # Should attempt gemini exactly once
    assert mock_gemini.structured_completion.call_count == 1
    # Groq should never be called
    mock_groq.structured_completion.assert_not_called()

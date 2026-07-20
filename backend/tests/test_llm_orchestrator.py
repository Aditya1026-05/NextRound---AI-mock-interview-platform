import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pydantic import BaseModel
import litellm

from app.core.config import settings
from app.core.exceptions import (
    AllProvidersUnavailableException,
    InvalidAIResponseException,
)
from app.llm.orchestrator import LLMOrchestrator, _is_transient_error


class MockResponseModel(BaseModel):
    name: str


@pytest.fixture(autouse=True)
def mock_fallback_settings():
    """Configure fallback order for deterministic unit tests."""
    with patch.object(settings, "LLM_PROVIDER", "gemini"), \
         patch.object(settings, "LLM_FALLBACK_ORDER", ["gemini", "groq"]):
        yield


def test_is_transient_error_detection():
    """Verify that transient network errors are correctly detected while validation/auth errors are not."""
    # 503 Service Unavailable Exception (transient)
    e_503 = Exception("VertexAIException - 503 unavailable Spikes in demand are temporary")
    assert _is_transient_error(e_503) is True

    # Connection timeout (transient)
    e_conn = litellm.exceptions.APIConnectionError("connection failure timeout", model="gemini", llm_provider="gemini")
    assert _is_transient_error(e_conn) is True

    # Pydantic validation error (non-transient)
    e_val = InvalidAIResponseException("Pydantic model validation failed: name required")
    assert _is_transient_error(e_val) is False

    # Authentication failure (non-transient)
    e_auth = litellm.exceptions.AuthenticationError("Authentication key is invalid", model="gemini", llm_provider="gemini")
    assert _is_transient_error(e_auth) is False


@pytest.mark.asyncio
@patch("app.llm.factory.LLMFactory.create_by_name")
async def test_llm_orchestrator_success_first_attempt(mock_create_by_name):
    """Test that the orchestrator returns successfully on the primary provider without fallback."""
    mock_gemini = MagicMock()
    mock_gemini.structured_completion = AsyncMock(return_value=MockResponseModel(name="Primary success"))
    mock_create_by_name.side_effect = lambda name: mock_gemini if name == "gemini" else None

    orchestrator = LLMOrchestrator()
    res = await orchestrator.structured_completion(
        system_prompt="sys",
        user_prompt="usr",
        response_model=MockResponseModel,
    )

    assert res.name == "Primary success"
    mock_gemini.structured_completion.assert_called_once()
    mock_create_by_name.assert_called_once_with("gemini")


@pytest.mark.asyncio
@patch("app.llm.factory.LLMFactory.create_by_name")
async def test_llm_orchestrator_fallback_success(mock_create_by_name):
    """Test that transient errors on the primary provider cause a fallback to the secondary provider."""
    mock_gemini = MagicMock()
    # Mock VertexAI 503 temporary service unavailable error
    mock_gemini.structured_completion = AsyncMock(side_effect=Exception("VertexAIException - 503 unavailable demand spikes"))

    mock_groq = MagicMock()
    mock_groq.structured_completion = AsyncMock(return_value=MockResponseModel(name="Fallback success"))

    def create_mock(name):
        if name == "gemini":
            return mock_gemini
        elif name == "groq":
            return mock_groq
        return None
    mock_create_by_name.side_effect = create_mock

    orchestrator = LLMOrchestrator()
    res = await orchestrator.structured_completion(
        system_prompt="sys",
        user_prompt="usr",
        response_model=MockResponseModel,
    )

    assert res.name == "Fallback success"
    mock_gemini.structured_completion.assert_called_once()
    mock_groq.structured_completion.assert_called_once()


@pytest.mark.asyncio
@patch("app.llm.factory.LLMFactory.create_by_name")
async def test_llm_orchestrator_non_transient_no_fallback(mock_create_by_name):
    """Test that non-transient exceptions (like validation errors) abort immediately without fallback."""
    mock_gemini = MagicMock()
    mock_gemini.structured_completion = AsyncMock(side_effect=InvalidAIResponseException("Pydantic validation failed"))

    mock_groq = MagicMock()
    mock_groq.structured_completion = AsyncMock()

    mock_create_by_name.side_effect = lambda name: mock_gemini if name == "gemini" else mock_groq

    orchestrator = LLMOrchestrator()
    with pytest.raises(InvalidAIResponseException):
        await orchestrator.structured_completion(
            system_prompt="sys",
            user_prompt="usr",
            response_model=MockResponseModel,
        )

    mock_gemini.structured_completion.assert_called_once()
    mock_groq.structured_completion.assert_not_called()


@pytest.mark.asyncio
@patch("app.llm.factory.LLMFactory.create_by_name")
async def test_llm_orchestrator_all_providers_fail(mock_create_by_name):
    """Test that if all providers hit transient failures, AllProvidersUnavailableException is raised."""
    mock_gemini = MagicMock()
    mock_gemini.structured_completion = AsyncMock(side_effect=Exception("503 temporary unavailable"))

    mock_groq = MagicMock()
    mock_groq.structured_completion = AsyncMock(side_effect=Exception("429 rate limit exceeded"))

    def create_mock(name):
        if name == "gemini":
            return mock_gemini
        elif name == "groq":
            return mock_groq
        return None
    mock_create_by_name.side_effect = create_mock

    orchestrator = LLMOrchestrator()
    with pytest.raises(AllProvidersUnavailableException) as exc_info:
        await orchestrator.structured_completion(
            system_prompt="sys",
            user_prompt="usr",
            response_model=MockResponseModel,
        )

    assert "All AI Providers are currently unavailable" in str(exc_info.value)
    mock_gemini.structured_completion.assert_called_once()
    mock_groq.structured_completion.assert_called_once()

import time
import litellm
from pydantic import BaseModel
from structlog import get_logger

from app.core.config import settings
from app.core.exceptions import AllProvidersUnavailableException, AIProviderUnavailableException
from app.llm.factory import LLMFactory

logger = get_logger()


def _is_transient_error(e: Exception) -> bool:
    """Helper to detect transient provider/network errors vs configuration/validation errors."""
    cause = e.__cause__ or e

    # 1. Check known LiteLLM transient exceptions
    if isinstance(cause, (
        litellm.exceptions.APIConnectionError,
        litellm.exceptions.RateLimitError,
        litellm.exceptions.ServiceUnavailableError,
        litellm.exceptions.Timeout
    )):
        return True

    # 2. Check APIError status codes (e.g. 429, 500, 502, 503, 504)
    if isinstance(cause, litellm.exceptions.APIError):
        status_code = getattr(cause, "status_code", None)
        if status_code in (429, 500, 502, 503, 504):
            return True

    # 3. Check custom app exception mappings
    if isinstance(e, AIProviderUnavailableException):
        return True

    # 4. Check strings/substrings of the error message for safety (e.g. 503, 429, timeout)
    err_str = str(cause).lower()
    transient_keywords = [
        "503", "429", "500", "502", "504", "timeout", "unavailable",
        "rate limit", "connection failure", "high demand", "temporary"
    ]
    # Ensure we don't treat validation errors or authentication/API key issues as transient
    if any(kw in err_str for kw in transient_keywords):
        non_transient_keywords = ["validation", "api_key", "invalid key", "authentication", "api key", "json", "401", "403"]
        if not any(nt in err_str for nt in non_transient_keywords):
            return True

    return False


class LLMOrchestrator:
    """Orchestrates structured LLM completions across multiple providers with fallbacks, retries, and error logging."""

    async def structured_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        """Call structured completion iterating through priority list on transient failures."""
        errors = []

        primary_provider = settings.LLM_PROVIDER.lower().strip()
        fallback_order = [primary_provider]
        for p in settings.LLM_FALLBACK_ORDER:
            p_clean = p.lower().strip()
            if p_clean not in fallback_order:
                fallback_order.append(p_clean)

        for provider_name in fallback_order:
            start_time = time.time()
            logger.info("Attempting structured LLM completion", provider=provider_name)
            try:
                provider = LLMFactory.create_by_name(provider_name)
                result = await provider.structured_completion(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_model=response_model,
                )
                duration = time.time() - start_time
                logger.info(
                    "Structured LLM completion succeeded",
                    provider=provider_name,
                    duration_seconds=duration,
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    "Structured LLM completion failed",
                    provider=provider_name,
                    duration_seconds=duration,
                    error=str(e),
                )

                if _is_transient_error(e):
                    errors.append(f"{provider_name}: {e}")
                    logger.warn(
                        "Transient error encountered, attempting fallback",
                        failed_provider=provider_name,
                        error=str(e),
                    )
                    continue
                else:
                    logger.error(
                        "Non-transient error encountered, aborting fallback chain",
                        provider=provider_name,
                        error=str(e),
                    )
                    raise e

        aggregate_detail = "All AI Providers are currently unavailable: " + "; ".join(errors)
        raise AllProvidersUnavailableException(detail=aggregate_detail)

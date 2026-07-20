import asyncio
import time

import litellm
from pydantic import BaseModel
from structlog import get_logger

from app.core.exceptions import (
    AIProviderUnavailableException,
    AllProvidersUnavailableException,
)
from app.llm.factory import LLMFactory
from app.llm.registry import CompletionOverrides, LLMRegistry

logger = get_logger()


def _is_transient_error(e: Exception) -> bool:
    """Helper to detect transient provider/network errors vs configuration/validation errors."""
    cause = e.__cause__ or e

    # 1. Check known LiteLLM transient exceptions
    if isinstance(
        cause,
        (
            litellm.exceptions.APIConnectionError,
            litellm.exceptions.RateLimitError,
            litellm.exceptions.ServiceUnavailableError,
            litellm.exceptions.Timeout,
        ),
    ):
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
        "503",
        "429",
        "500",
        "502",
        "504",
        "timeout",
        "unavailable",
        "rate limit",
        "connection failure",
        "high demand",
        "temporary",
    ]
    # Ensure we don't treat validation errors or authentication/API key issues as transient
    if any(kw in err_str for kw in transient_keywords):
        non_transient_keywords = [
            "validation",
            "api_key",
            "invalid key",
            "authentication",
            "api key",
            "json",
            "401",
            "403",
        ]
        if not any(nt in err_str for nt in non_transient_keywords):
            return True

    return False


class LLMOrchestrator:
    """Orchestrates structured LLM completions across multiple providers with fallbacks, retries, and error logging."""

    def __init__(self, registry: LLMRegistry | None = None):
        self.registry = registry or LLMRegistry()

    async def structured_completion(
        self,
        *,
        profile: str,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        overrides: CompletionOverrides | None = None,
    ) -> BaseModel:
        """Call structured completion iterating through logical profile registry fallback chain on transient failures."""
        errors = []

        # Resolve the logical profile configuration (raises KeyError if not found)
        profile_cfg = self.registry.get_profile(profile)

        # Build the fallback chain: primary model followed by fallback list
        fallback_chain = [profile_cfg.primary]
        for fb in profile_cfg.fallbacks:
            if fb not in fallback_chain:
                fallback_chain.append(fb)

        max_attempts = max(1, profile_cfg.retries + 1)
        retry_delay = profile_cfg.retry_delay

        for model_name in fallback_chain:
            # Resolve model registry config
            model_cfg = self.registry.get_model(model_name)
            provider_name = model_cfg.provider
            litellm_model = model_cfg.model

            # Bind base parameters
            temp = model_cfg.temperature
            tokens = model_cfg.max_tokens
            timeout_limit = model_cfg.timeout

            # Apply type-safe dynamic overrides if specified
            if overrides:
                if overrides.temperature is not None:
                    temp = overrides.temperature
                if overrides.max_tokens is not None:
                    tokens = overrides.max_tokens
                if overrides.timeout is not None:
                    timeout_limit = overrides.timeout

            # Attempt completions up to retry limit
            for attempt in range(1, max_attempts + 1):
                start_time = time.time()
                logger.info(f"Using provider: {provider_name.capitalize()}")
                logger.info(f"Attempt {attempt}")
                try:
                    provider = LLMFactory.create_by_name(provider_name)
                    result = await provider.structured_completion(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        response_model=response_model,
                        model_name=litellm_model,
                        temperature=temp,
                        max_tokens=tokens,
                        timeout=timeout_limit,
                    )
                    duration = time.time() - start_time
                    logger.info(f"{provider_name.capitalize()} succeeded in {duration:.1f}s")
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(f"{provider_name.capitalize()} failed in {duration:.1f}s - Error: {e}")

                    if _is_transient_error(e):
                        errors.append(f"{model_name} (attempt {attempt}/{max_attempts}): {e}")

                        if attempt < max_attempts:
                            logger.warn(f"Transient error. Sleeping {retry_delay}s before retry...")
                            await asyncio.sleep(retry_delay)
                        else:
                            # Let's check if there is a next model in the fallback chain to name it in the logs
                            current_index = fallback_chain.index(model_name)
                            if current_index + 1 < len(fallback_chain):
                                next_model = fallback_chain[current_index + 1]
                                next_model_cfg = self.registry.get_model(next_model)
                                logger.warn(
                                    f"All attempts failed. Falling back to {next_model_cfg.provider.capitalize()}..."
                                )
                            else:
                                logger.warn("All attempts failed. No further fallbacks available.")
                    else:
                        logger.error("Non-transient error. Aborting fallback chain.")
                        raise e

        aggregate_detail = (
            f"All AI Providers exhausted for profile '{profile}': " + "; ".join(errors)
        )
        raise AllProvidersUnavailableException(detail=aggregate_detail)

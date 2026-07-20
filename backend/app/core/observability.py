import functools
import inspect
import time
from typing import Any

import structlog

logger = structlog.get_logger()


def bind_context(**kwargs) -> None:
    """Bind allowed business identifiers to the structured logging context.
    Filters out non-observability keys to prevent logging pollution.
    """
    allowed_keys = {
        "request_id",
        "user_id",
        "resume_id",
        "candidate_profile_id",
        "session_id",
        "blueprint_id",
        "profile",
        "provider",
        "model",
    }
    filtered = {
        k: str(v) for k, v in kwargs.items() if k in allowed_keys and v is not None
    }
    if filtered:
        structlog.contextvars.bind_contextvars(**filtered)


def clear_context() -> None:
    """Clear all active variables from the thread-local log context."""
    structlog.contextvars.clear_contextvars()


class log_operation:  # noqa: N801
    """Centralized timing context manager and decorator.
    Measures block duration and logs execution status consistently.
    """

    def __init__(self, category: str, name: str):
        self.category = category
        self.name = name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        logger.info(
            f"Starting operation: {self.name}",
            category=self.category,
            status="started",
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start_time
        if exc_type is not None:
            logger.error(
                f"✗ {self.name} failed after {duration:.2f}s",
                category=self.category,
                status="failed",
                duration_seconds=duration,
                error_type=exc_type.__name__,
                error_msg=str(exc_val),
            )
        else:
            logger.info(
                f"✓ {self.name} completed successfully in {duration:.2f}s",
                category=self.category,
                status="completed",
                duration_seconds=duration,
            )
        return False

    async def __aenter__(self):
        self.start_time = time.perf_counter()
        logger.info(
            f"Starting operation: {self.name}",
            category=self.category,
            status="started",
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start_time
        if exc_type is not None:
            logger.error(
                f"✗ {self.name} failed after {duration:.2f}s",
                category=self.category,
                status="failed",
                duration_seconds=duration,
                error_type=exc_type.__name__,
                error_msg=str(exc_val),
            )
        else:
            logger.info(
                f"✓ {self.name} completed successfully in {duration:.2f}s",
                category=self.category,
                status="completed",
                duration_seconds=duration,
            )
        return False

    def __call__(self, func):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                async with self:
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self:
                    return func(*args, **kwargs)
            return sync_wrapper


def step_started(category: str, step_name: str, **kwargs) -> None:
    """Log the initialization of a business workflow sub-step."""
    logger.info(
        f"  Starting step: {step_name}", category=category, step=step_name, **kwargs
    )


def step_completed(category: str, step_name: str, **kwargs) -> None:
    """Log the successful completion of a business workflow sub-step."""
    logger.info(
        f"  ✓ {step_name}",
        category=category,
        step=step_name,
        status="completed",
        **kwargs,
    )


def step_failed(category: str, step_name: str, error: Any, **kwargs) -> None:
    """Log the failure of a business workflow sub-step."""
    err_msg = str(error)
    logger.error(
        f"  ✗ {step_name} failed: {err_msg}",
        category=category,
        step=step_name,
        status="failed",
        error=err_msg,
        **kwargs,
    )


def provider_selected(
    profile: str, primary: str, fallbacks: list[str], category: str = "LLM"
) -> None:
    """Log LLM logical profile metadata and its execution model map."""
    logger.info(
        f"LLM Profile Selected:\nProfile: {profile}\nPrimary: {primary}\nFallback: {' -> '.join(fallbacks) if fallbacks else 'None'}",
        category=category,
        profile=profile,
        primary_provider=primary,
        fallback_chain=fallbacks,
    )


def provider_trying(provider: str, model: str, category: str = "LLM") -> None:
    """Log the current provider and model being targeted."""
    logger.info(
        f"Trying Provider: {provider}\nModel: {model}",
        category=category,
        provider=provider,
        model=model,
    )


def provider_success(
    provider: str, duration: float, category: str = "LLM"
) -> None:
    """Log the success of an LLM completion request with timing details."""
    logger.info(
        f"✓ Provider Success\nLatency: {duration:.2f} seconds",
        category=category,
        provider=provider,
        latency=duration,
    )


def provider_retry(
    attempt: int, max_attempts: int, delay: float, category: str = "LLM"
) -> None:
    """Log a retry attempt on a transient LLM error."""
    logger.warning(
        f"Retry {attempt}/{max_attempts} after transient delay {delay}s",
        category=category,
        attempt=attempt,
        max_attempts=max_attempts,
        retry_delay=delay,
    )


def provider_fallback(
    failed_provider: str,
    next_provider: str,
    reason: str,
    category: str = "LLM",
) -> None:
    """Log a provider fallback trigger."""
    logger.warning(
        f"{failed_provider} failed ({reason}). Falling back to {next_provider}...",
        category=category,
        failed_provider=failed_provider,
        next_provider=next_provider,
        reason=reason,
    )


def providers_all_failed(errors: dict[str, str], category: str = "LLM") -> None:
    """Log the critical state when all LLM providers have failed."""
    err_summary = "\n".join(f"{p} -> {err}" for p, err in errors.items())
    logger.critical(
        f"All providers unavailable\n{err_summary}",
        category=category,
        errors=errors,
    )


def transaction_started(category: str = "DATABASE") -> None:
    """Log database transaction/savepoint boundaries start."""
    logger.info("Database Transaction Started", category=category)


def transaction_committed(category: str = "DATABASE") -> None:
    """Log database transaction/savepoint successful commit."""
    logger.info("Transaction Committed", category=category)


def transaction_rolled_back(
    error: Any, category: str = "DATABASE"
) -> None:
    """Log database transaction/savepoint rollback event."""
    logger.error(
        f"Transaction Rolled Back: {error}", category=category, error=str(error)
    )

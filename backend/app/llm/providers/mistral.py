import json
import os

import litellm
import structlog
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import (
    AIProviderUnavailableException,
    InvalidAIResponseException,
    LLMProviderException,
)
from app.llm.base import LLMProvider

logger = structlog.get_logger()


class MistralProvider(LLMProvider):
    """LLM provider targeting Mistral API via LiteLLM interface."""

    def __init__(self):
        self.api_key = settings.MISTRAL_API_KEY
        if self.api_key:
            os.environ["MISTRAL_API_KEY"] = self.api_key

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
        if not self.api_key:
            logger.error("Mistral API key is not configured")
            raise AIProviderUnavailableException(
                detail="Mistral API key is missing"
            )

        target_model = model_name or "mistral/mistral-small"
        target_temp = 0.2 if temperature is None else temperature
        target_tokens = 2048 if max_tokens is None else max_tokens
        target_timeout = 15 if timeout is None else timeout

        try:
            response = await litellm.acompletion(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=target_temp,
                max_tokens=target_tokens,
                timeout=target_timeout,
                response_format={"type": "json_object"},
            )
        except litellm.exceptions.APIConnectionError as e:
            logger.error("Mistral connection failure", error=str(e))
            raise AIProviderUnavailableException(
                detail="Could not connect to Mistral API"
            ) from e
        except litellm.exceptions.RateLimitError as e:
            logger.error("Mistral rate limit exceeded", error=str(e))
            raise AIProviderUnavailableException(
                detail="Mistral API rate limit exceeded"
            ) from e
        except Exception as e:
            logger.error("LiteLLM completion request failed for Mistral", error=str(e))
            raise LLMProviderException(
                detail=f"LiteLLM completion request failed: {e!s}"
            ) from e

        try:
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response content from LLM")
            data = json.loads(content)
            if isinstance(data, dict) and len(data) == 1:
                root_key = next(iter(data))
                if isinstance(data[root_key], dict) and not any(k in data for k in response_model.model_fields):
                    logger.info("Unwrapping nested LLM response root key", root_key=root_key)
                    data = data[root_key]
            return response_model.model_validate(data)
        except json.JSONDecodeError as e:
            logger.error("Failed to decode LLM JSON response", error=str(e))
            raise InvalidAIResponseException(
                detail="LLM output is not valid JSON"
            ) from e
        except Exception as e:
            logger.error(
                "Parsed response model validation failed", error=str(e)
            )
            raise InvalidAIResponseException(
                detail=f"Pydantic model validation failed: {e!s}"
            ) from e

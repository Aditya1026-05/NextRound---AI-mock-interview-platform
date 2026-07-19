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


class GeminiProvider(LLMProvider):
    """LLM provider targeting Google Gemini API via LiteLLM interface."""

    def __init__(self):
        # Configure Gemini API key in environment
        self.api_key = settings.GEMINI_API_KEY or settings.LITELLM_GEMINI_API_KEY
        if self.api_key:
            os.environ["GEMINI_API_KEY"] = self.api_key

    async def structured_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        if not self.api_key:
            logger.error("Gemini API key is not configured")
            raise AIProviderUnavailableException(
                detail="Gemini API key is missing"
            )

        try:
            response = await litellm.acompletion(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                timeout=settings.LLM_TIMEOUT,
                response_format={"type": "json_object"},
            )
        except litellm.exceptions.APIConnectionError as e:
            logger.error("Gemini connection failure", error=str(e))
            raise AIProviderUnavailableException(
                detail="Could not connect to Gemini API"
            ) from e
        except litellm.exceptions.RateLimitError as e:
            logger.error("Gemini rate limit exceeded", error=str(e))
            raise AIProviderUnavailableException(
                detail="Gemini API rate limit exceeded"
            ) from e
        except Exception as e:
            logger.error("LiteLLM completion request failed", error=str(e))
            raise LLMProviderException(
                detail=f"LiteLLM completion request failed: {e!s}"
            ) from e

        try:
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response content from LLM")
            data = json.loads(content)
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

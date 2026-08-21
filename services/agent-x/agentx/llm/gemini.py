"""Gemini LLM Provider Implementation using Google Gen AI SDK."""

import json
from typing import TypeVar

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from agentx.llm.base import (
    LLMAuthenticationError,
    LLMError,
    LLMProvider,
    LLMResourceExhaustedError,
)
from agentx_common.constants import MODELS

T = TypeVar("T", bound=BaseModel)


class GeminiLLMProvider(LLMProvider):
    """Production LLM provider using Gemini 2.5 Pro and Flash via Google Gen AI SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = MODELS.REASONING_PRO,
    ) -> None:
        self.default_model = default_model
        try:
            self.client = genai.Client(api_key=api_key) if api_key else genai.Client()
        except Exception as e:
            raise LLMAuthenticationError(f"Failed to initialize Google Gen AI Client: {e}") from e

    def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None = None,
        temperature: float = 0.1,
        max_output_tokens: int | None = None,
    ) -> T:
        """Generate structured JSON output validated against response_schema."""
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=response_schema,
            max_output_tokens=max_output_tokens,
        )

        try:
            response = self.client.models.generate_content(
                model=self.default_model,
                contents=prompt,
                config=config,
            )
            raw_text = response.text or "{}"
            return response_schema.model_validate_json(raw_text)
        except errors.APIError as e:
            if e.code == 429:
                raise LLMResourceExhaustedError(f"Gemini API rate limit exceeded: {e}") from e
            if e.code in (401, 403):
                raise LLMAuthenticationError(f"Gemini API authentication failure: {e}") from e
            raise LLMError(f"Gemini API Error [{e.code}]: {e.message}") from e
        except (ValidationError, json.JSONDecodeError) as e:
            raise LLMError(
                f"Failed to parse model response into schema {response_schema.__name__}: {e}"
            ) from e
        except Exception as e:
            raise LLMError(f"Unexpected error during structured Gemini generation: {e}") from e

    def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
        max_output_tokens: int | None = None,
    ) -> str:
        """Generate standard unstructured text output."""
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

        try:
            response = self.client.models.generate_content(
                model=self.default_model,
                contents=prompt,
                config=config,
            )
            return response.text or ""
        except errors.APIError as e:
            if e.code == 429:
                raise LLMResourceExhaustedError(f"Gemini API rate limit exceeded: {e}") from e
            if e.code in (401, 403):
                raise LLMAuthenticationError(f"Gemini API authentication failure: {e}") from e
            raise LLMError(f"Gemini API Error [{e.code}]: {e.message}") from e
        except Exception as e:
            raise LLMError(f"Unexpected error during Gemini text generation: {e}") from e

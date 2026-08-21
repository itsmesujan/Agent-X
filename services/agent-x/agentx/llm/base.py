"""Agent-X LLM Provider Abstract Base Interface."""

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Base exception for LLM provider errors."""

    pass


class LLMAuthenticationError(LLMError):
    """Raised when LLM credentials/API keys are invalid or missing."""

    pass


class LLMResourceExhaustedError(LLMError):
    """Raised on HTTP 429 / rate limits."""

    pass


class LLMProvider(ABC):
    """Abstract interface for interacting with Large Language Models."""

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None = None,
        temperature: float = 0.1,
        max_output_tokens: int | None = None,
    ) -> T:
        """Generate a response constrained to a Pydantic schema."""
        pass

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
        max_output_tokens: int | None = None,
    ) -> str:
        """Generate unstructured text content."""
        pass

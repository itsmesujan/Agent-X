"""Mock LLM Provider for deterministic testing."""

from typing import Any, TypeVar

from pydantic import BaseModel

from agentx.llm.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """Deterministic Mock LLM Provider for unit tests."""

    def __init__(
        self,
        default_structured_response: BaseModel | None = None,
        default_text_response: str = "Mocked LLM text response",
    ) -> None:
        self.default_structured_response = default_structured_response
        self.default_text_response = default_text_response
        self.calls: list[dict[str, Any]] = []
        self._schema_responses: dict[type, Any] = {}
        self.exception_to_raise: Exception | None = None

    def register_response(self, response_schema: type[T], response_instance: T) -> None:
        """Register a specific mock instance for a given Pydantic schema."""
        self._schema_responses[response_schema] = response_instance

    def register_structured_response(self, response_schema: type[T], response_instance: T) -> None:
        """Alias for register_response."""
        self.register_response(response_schema, response_instance)

    def set_exception(self, exc: Exception | None) -> None:
        """Configure the mock to raise a specific exception upon call."""
        self.exception_to_raise = exc

    def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None = None,
        temperature: float = 0.1,
        max_output_tokens: int | None = None,
    ) -> T:
        self.calls.append(
            {
                "type": "structured",
                "prompt": prompt,
                "schema": response_schema,
                "system_instruction": system_instruction,
                "temperature": temperature,
            }
        )

        if self.exception_to_raise:
            raise self.exception_to_raise

        if response_schema in self._schema_responses:
            res = self._schema_responses[response_schema]
            if isinstance(res, response_schema):
                return res

        if self.default_structured_response and isinstance(
            self.default_structured_response, response_schema
        ):
            return self.default_structured_response

        # Fallback: instantiate response_schema with minimal dummy values
        raise ValueError(
            f"MockLLMProvider has no registered response for schema '{response_schema.__name__}'"
        )

    def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
        max_output_tokens: int | None = None,
    ) -> str:
        self.calls.append(
            {
                "type": "text",
                "prompt": prompt,
                "system_instruction": system_instruction,
                "temperature": temperature,
            }
        )

        if self.exception_to_raise:
            raise self.exception_to_raise

        return self.default_text_response

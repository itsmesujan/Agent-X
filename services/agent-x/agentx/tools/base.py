"""Agent-X Base Tool Abstract Class."""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any

from agentx.tools.schemas import (
    ToolDeclaration,
    ToolExecutionResult,
    ToolInvocationContext,
    ToolSecurityError,
)


class BaseTool(ABC):
    """Abstract base class for all callable tools in Agent-X."""

    def __init__(self, declaration: ToolDeclaration) -> None:
        self.declaration = declaration

    @property
    def name(self) -> str:
        return self.declaration.name

    @property
    def description(self) -> str:
        return self.declaration.description

    @property
    def timeout(self) -> float:
        return self.declaration.timeout

    async def execute(self, context: ToolInvocationContext) -> ToolExecutionResult:
        """Executes the tool with strict timeout gating, cost tracking, and fault containment."""
        start_time = time.perf_counter()

        try:
            # Enforce tool timeout
            output_dict = await asyncio.wait_for(
                self._run(context.parameters, context),
                timeout=self.declaration.timeout,
            )

            duration_ms = (time.perf_counter() - start_time) * 1000.0
            artifacts = output_dict.pop("__artifacts__", [])
            untrusted = bool(output_dict.pop("__untrusted__", False))

            return ToolExecutionResult(
                tool_name=self.name,
                is_success=True,
                data=output_dict,
                artifacts=artifacts,
                untrusted_data_flag=untrusted,
                duration_ms=round(duration_ms, 2),
                cost_usd=self.declaration.estimated_cost,
            )

        except TimeoutError:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolExecutionResult(
                tool_name=self.name,
                is_success=False,
                error_message=f"Tool '{self.name}' timed out after {self.declaration.timeout:.2f}s",
                duration_ms=round(duration_ms, 2),
                cost_usd=0.0,
            )

        except ToolSecurityError as sec_err:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolExecutionResult(
                tool_name=self.name,
                is_success=False,
                error_message=f"SECURITY_DENIED: {str(sec_err)}",
                duration_ms=round(duration_ms, 2),
                cost_usd=0.0,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolExecutionResult(
                tool_name=self.name,
                is_success=False,
                error_message=f"{type(e).__name__}: {str(e)}",
                duration_ms=round(duration_ms, 2),
                cost_usd=0.0,
            )

    @abstractmethod
    async def _run(
        self, parameters: dict[str, Any], context: ToolInvocationContext
    ) -> dict[str, Any]:
        """Internal tool execution implementation.

        Return a dictionary of output values, and optionally:
        - '__artifacts__': list[dict[str, Any]]
        - '__untrusted__': bool (True if returning untrusted external content)
        """
        pass

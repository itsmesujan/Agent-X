"""Agent-X Base Agent Abstract Class."""

import time
from abc import ABC, abstractmethod
from typing import Any

from agentx.llm.base import LLMProvider
from agentx.llm.mock import MockLLMProvider
from agentx.runtime.schemas import (
    AgentInvocationContext,
    AgentResult,
    AgentStatus,
    AgentType,
)


class BaseAgent(ABC):
    """Abstract base class for all specialized agents in Agent-X."""

    def __init__(
        self,
        agent_type: AgentType,
        name: str | None = None,
        description: str | None = None,
        capabilities: list[str] | None = None,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self.agent_type = agent_type
        self.name = name or agent_type.value.title() + "Agent"
        self.description = description or f"Specialized agent for {agent_type.value}"
        self.capabilities = capabilities or []
        self.llm_provider = llm_provider or MockLLMProvider()

    async def execute(self, context: AgentInvocationContext) -> AgentResult:
        """Executes a task within the agent boundary, measuring performance and handling faults."""
        start_time = time.perf_counter()

        try:
            # 1. Execute agent-specific domain logic
            output_payload = await self._execute_internal(context)

            duration_ms = (time.perf_counter() - start_time) * 1000.0
            artifacts = output_payload.pop("__artifacts__", [])
            confidence = float(output_payload.pop("__confidence__", 1.0))
            tokens_used = int(output_payload.pop("__tokens_used__", 1200))
            cost_usd = float(output_payload.pop("__cost_usd__", 0.0003))

            return AgentResult(
                task_id=context.task_id,
                agent_type=self.agent_type,
                status=AgentStatus.SUCCESS,
                output_data=output_payload,
                artifacts=artifacts,
                confidence_score=confidence,
                execution_time_ms=round(duration_ms, 2),
                tokens_used=tokens_used,
                cost_usd=cost_usd,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return AgentResult(
                task_id=context.task_id,
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error_details=f"{type(e).__name__}: {str(e)}",
                execution_time_ms=round(duration_ms, 2),
            )

    @abstractmethod
    async def _execute_internal(self, context: AgentInvocationContext) -> dict[str, Any]:
        """Internal domain execution logic implemented by specialized agent subclasses.

        May return dict containing structured domain keys, plus optional special metadata:
        - '__artifacts__': list[dict[str, Any]]
        - '__confidence__': float (0.0 to 1.0)
        - '__tokens_used__': int
        - '__cost_usd__': float
        """
        pass

"""Agent-X Central Agent Runtime Engine."""

import asyncio
import time
from typing import overload

from agentx.kernel.events import EventBus
from agentx.runtime.agents.analyst import AnalystAgent
from agentx.runtime.agents.artifact import ArtifactAgent
from agentx.runtime.agents.critic import CriticAgent
from agentx.runtime.agents.planner import PlannerAgent
from agentx.runtime.agents.recovery import RecoveryAgent
from agentx.runtime.agents.researcher import ResearcherAgent
from agentx.runtime.agents.verifier import VerifierAgent
from agentx.runtime.base import BaseAgent
from agentx.runtime.capabilities import CapabilityRegistry
from agentx.runtime.metrics import AgentMetricsTracker
from agentx.runtime.registry import AgentRegistry
from agentx.runtime.schemas import (
    AgentInvocationContext,
    AgentPerformanceMetrics,
    AgentResult,
    AgentStatus,
    AgentType,
)


class AgentRuntime:
    """Central engine orchestrating agent lifecycle, capability discovery, timeout enforcement, and metrics."""

    def __init__(
        self,
        agent_registry: AgentRegistry | None = None,
        capability_registry: CapabilityRegistry | None = None,
        metrics_tracker: AgentMetricsTracker | None = None,
        event_bus: EventBus | None = None,
        auto_register_default_agents: bool = True,
    ) -> None:
        self.capability_registry = capability_registry or CapabilityRegistry()
        self.agent_registry = agent_registry or AgentRegistry(
            capability_registry=self.capability_registry
        )
        self.metrics_tracker = metrics_tracker or AgentMetricsTracker()
        self.event_bus = event_bus or EventBus()

        if auto_register_default_agents:
            self._register_default_agents()

    def _register_default_agents(self) -> None:
        """Instantiate and register the 7 core initial agents."""
        defaults: list[BaseAgent] = [
            PlannerAgent(),
            ResearcherAgent(),
            AnalystAgent(),
            VerifierAgent(),
            CriticAgent(),
            RecoveryAgent(),
            ArtifactAgent(),
        ]
        for agent in defaults:
            self.agent_registry.register_agent(agent)

    async def invoke(
        self,
        agent_identifier: AgentType | str,
        context: AgentInvocationContext,
        timeout_seconds: float | None = None,
    ) -> AgentResult:
        """Invokes a specialized agent with strict timeout gating, fault isolation, and metrics recording."""
        start_time = time.perf_counter()
        agent = self.agent_registry.get_agent(agent_identifier)
        effective_timeout = timeout_seconds or context.timeout_seconds

        try:
            # Enforce timeout boundary
            result = await asyncio.wait_for(
                agent.execute(context),
                timeout=effective_timeout,
            )

            is_success = result.status == AgentStatus.SUCCESS
            self.metrics_tracker.record_invocation(
                agent_type=agent.agent_type,
                duration_ms=result.execution_time_ms,
                is_success=is_success,
                is_timeout=False,
                tokens_used=result.tokens_used,
                cost_usd=result.cost_usd,
            )
            return result

        except TimeoutError:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            self.metrics_tracker.record_invocation(
                agent_type=agent.agent_type,
                duration_ms=duration_ms,
                is_success=False,
                is_timeout=True,
            )
            return AgentResult(
                task_id=context.task_id,
                agent_type=agent.agent_type,
                status=AgentStatus.TIMEOUT,
                error_details=f"Agent '{agent.name}' exceeded timeout of {effective_timeout:.2f}s",
                execution_time_ms=round(duration_ms, 2),
            )

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            self.metrics_tracker.record_invocation(
                agent_type=agent.agent_type,
                duration_ms=duration_ms,
                is_success=False,
                is_timeout=False,
            )
            return AgentResult(
                task_id=context.task_id,
                agent_type=agent.agent_type,
                status=AgentStatus.FAILED,
                error_details=f"{type(exc).__name__}: {str(exc)}",
                execution_time_ms=round(duration_ms, 2),
            )

    @overload
    def get_metrics(self, agent_type: AgentType | str) -> AgentPerformanceMetrics: ...

    @overload
    def get_metrics(self, agent_type: None = None) -> dict[str, AgentPerformanceMetrics]: ...

    def get_metrics(
        self, agent_type: AgentType | str | None = None
    ) -> AgentPerformanceMetrics | dict[str, AgentPerformanceMetrics]:
        """Retrieve aggregated performance metrics for a specific agent or all agents."""
        if agent_type is not None:
            return self.metrics_tracker.get_metrics(agent_type)
        return self.metrics_tracker.get_all_metrics()

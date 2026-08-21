"""Agent-X Agent Runtime Performance and Telemetry Metrics Tracker."""

import threading
from typing import Any

from agentx.runtime.schemas import AgentPerformanceMetrics, AgentType


class AgentMetricsTracker:
    """Thread-safe telemetry and performance metrics tracker for agent executions."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._metrics: dict[str, dict[str, Any]] = {}
        self._init_metrics()

    def _init_metrics(self) -> None:
        """Initialize metric buckets for all known agent types and global."""
        for agent_type in AgentType:
            self._metrics[agent_type.value] = self._create_bucket(agent_type.value)
        self._metrics["GLOBAL"] = self._create_bucket("GLOBAL")

    def _create_bucket(self, name: str) -> dict[str, Any]:
        return {
            "agent_type": name,
            "total_invocations": 0,
            "success_count": 0,
            "failure_count": 0,
            "timeout_count": 0,
            "total_duration_ms": 0.0,
            "total_tokens_used": 0,
            "total_cost_usd": 0.0,
        }

    def record_invocation(
        self,
        agent_type: AgentType | str,
        duration_ms: float,
        is_success: bool,
        is_timeout: bool = False,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
    ) -> None:
        """Record an execution invocation outcome and update aggregate performance metrics."""
        type_key = agent_type.value if isinstance(agent_type, AgentType) else str(agent_type)

        with self._lock:
            if type_key not in self._metrics:
                self._metrics[type_key] = self._create_bucket(type_key)

            # Update specific agent bucket and global bucket
            for key in (type_key, "GLOBAL"):
                b = self._metrics[key]
                b["total_invocations"] += 1
                if is_success:
                    b["success_count"] += 1
                elif is_timeout:
                    b["timeout_count"] += 1
                else:
                    b["failure_count"] += 1

                b["total_duration_ms"] += max(0.0, duration_ms)
                b["total_tokens_used"] += max(0, tokens_used)
                b["total_cost_usd"] += max(0.0, cost_usd)

    def get_metrics(self, agent_type: AgentType | str) -> AgentPerformanceMetrics:
        """Retrieve computed performance metrics for a specific agent type."""
        type_key = agent_type.value if isinstance(agent_type, AgentType) else str(agent_type)

        with self._lock:
            b = self._metrics.get(type_key, self._create_bucket(type_key))
            total = b["total_invocations"]
            success = b["success_count"]
            rate = round((success / total) * 100.0, 2) if total > 0 else 100.0
            avg_dur = round(b["total_duration_ms"] / total, 2) if total > 0 else 0.0

            return AgentPerformanceMetrics(
                agent_type=type_key,
                total_invocations=total,
                success_count=success,
                failure_count=b["failure_count"],
                timeout_count=b["timeout_count"],
                total_duration_ms=round(b["total_duration_ms"], 2),
                avg_duration_ms=avg_dur,
                total_tokens_used=b["total_tokens_used"],
                total_cost_usd=round(b["total_cost_usd"], 6),
                success_rate=rate,
            )

    def get_all_metrics(self) -> dict[str, AgentPerformanceMetrics]:
        """Retrieve a dictionary of performance metrics across all agent types and global."""
        with self._lock:
            keys = list(self._metrics.keys())

        return {k: self.get_metrics(k) for k in keys}

    def reset(self) -> None:
        """Reset all tracked metrics to zero."""
        with self._lock:
            self._metrics.clear()
            self._init_metrics()

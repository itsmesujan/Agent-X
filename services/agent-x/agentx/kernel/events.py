"""Agent-X Kernel Event Subsystem."""

from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from agentx_common.schemas import MissionStatus, TaskStatus


class EventType(StrEnum):
    MISSION_CREATED = "MISSION_CREATED"
    MISSION_STATE_CHANGED = "MISSION_STATE_CHANGED"
    TASK_CREATED = "TASK_CREATED"
    TASK_STATE_CHANGED = "TASK_STATE_CHANGED"
    WORKFLOW_INITIALIZED = "WORKFLOW_INITIALIZED"
    WORKFLOW_MUTATED = "WORKFLOW_MUTATED"
    HITL_ESCALATION = "HITL_ESCALATION"
    VERIFICATION_RECORDED = "VERIFICATION_RECORDED"
    # Resource Brain Events
    RESOURCE_RESERVED = "RESOURCE_RESERVED"
    RESOURCE_CONSUMED = "RESOURCE_CONSUMED"
    RESOURCE_RELEASED = "RESOURCE_RELEASED"
    RESOURCE_REALLOCATED = "RESOURCE_REALLOCATED"
    BUDGET_WARNING = "BUDGET_WARNING"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    DEADLINE_WARNING = "DEADLINE_WARNING"
    DEADLINE_EXCEEDED = "DEADLINE_EXCEEDED"
    RATE_LIMIT_THROTTLED = "RATE_LIMIT_THROTTLED"
    HUMAN_ATTENTION_REQUESTED = "HUMAN_ATTENTION_REQUESTED"
    # Tool Execution Events
    TOOL_INVOKED = "TOOL_INVOKED"
    TOOL_FAILED = "TOOL_FAILED"
    # Recovery Events
    FAILURE_DIAGNOSED = "FAILURE_DIAGNOSED"
    RECOVERY_APPLIED = "RECOVERY_APPLIED"
    # Goal Drift Events
    GOAL_DRIFT_DETECTED = "GOAL_DRIFT_DETECTED"
    GOAL_DRIFT_REMEDIATED = "GOAL_DRIFT_REMEDIATED"


class KernelEvent(BaseModel):
    """Base event model for all kernel domain events."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(default_factory=lambda: f"evt_{uuid4().hex[:12]}")
    mission_id: str
    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = Field(default_factory=dict)


class MissionStateTransitionEvent(KernelEvent):
    """Emitted whenever a mission transitions between lifecycle states."""

    event_type: EventType = EventType.MISSION_STATE_CHANGED
    from_status: MissionStatus | None = None
    to_status: MissionStatus
    reason: str | None = None


class TaskStateTransitionEvent(KernelEvent):
    """Emitted whenever a task transitions between execution states."""

    event_type: EventType = EventType.TASK_STATE_CHANGED
    task_id: str
    from_status: TaskStatus | None = None
    to_status: TaskStatus
    retry_count: int = 0
    worker_id: str | None = None
    error_message: str | None = None


class WorkflowMutatedEvent(KernelEvent):
    """Emitted when tasks are dynamically injected, pruned, or remapped in a workflow."""

    event_type: EventType = EventType.WORKFLOW_MUTATED
    mutation_type: str  # "INJECT_SUBTREE" | "SKIP_BRANCH" | "ADD_TASK"
    affected_task_ids: list[str] = Field(default_factory=list)
    reason: str


class HITLEscalationEvent(KernelEvent):
    """Emitted when autonomous recovery fails and human intervention is required."""

    event_type: EventType = EventType.HITL_ESCALATION
    task_id: str
    error_class: str
    diagnosis: str
    suggested_actions: list[str] = Field(default_factory=list)


class ResourceEvent(KernelEvent):
    """Emitted for all resource ledger mutations and budget/quota threshold alerts."""

    task_id: str | None = None
    mutation_type: (
        str  # "RESERVATION" | "CONSUMPTION" | "RELEASE" | "REALLOCATION" | "WARNING" | "EXHAUSTED"
    )
    amount_usd: float = 0.0
    tokens: int = 0
    duration_seconds: int = 0
    details: dict[str, Any] = Field(default_factory=dict)


class ToolExecutionEvent(KernelEvent):
    """Emitted whenever a tool is invoked or completes execution."""

    tool_name: str
    task_id: str | None = None
    agent_type: str | None = None
    status: str = "SUCCESS"  # "SUCCESS" | "FAILED" | "TIMEOUT" | "SECURITY_DENIED"
    risk_level: str = "LOW"
    duration_ms: float = 0.0
    cost_usd: float = 0.0
    error_message: str | None = None


class EventBus:
    """Thread-safe in-memory event bus for publishing and subscribing to kernel events."""

    def __init__(self) -> None:
        self._subscribers: dict[EventType, list[Callable[[KernelEvent], None]]] = {
            t: [] for t in EventType
        }
        self._global_subscribers: list[Callable[[KernelEvent], None]] = []
        self._history: list[KernelEvent] = []

    def subscribe(
        self,
        event_type: EventType,
        callback: Callable[[KernelEvent], None],
    ) -> None:
        """Register a callback for a specific event type."""
        self._subscribers[event_type].append(callback)

    def subscribe_all(self, callback: Callable[[KernelEvent], None]) -> None:
        """Register a callback for all published events."""
        self._global_subscribers.append(callback)

    def publish(self, event: KernelEvent) -> None:
        """Publish an event to all registered listeners and record in history."""
        self._history.append(event)
        for cb in self._subscribers.get(event.event_type, []):
            cb(event)
        for cb in self._global_subscribers:
            cb(event)

    def get_events(self, mission_id: str | None = None) -> list[KernelEvent]:
        """Retrieve recorded event history, optionally filtered by mission_id."""
        if mission_id is None:
            return list(self._history)
        return [e for e in self._history if e.mission_id == mission_id]

    def clear(self) -> None:
        """Clear event history and subscriptions."""
        self._history.clear()
        self._subscribers = {t: [] for t in EventType}
        self._global_subscribers.clear()

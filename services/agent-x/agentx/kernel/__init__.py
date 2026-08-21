"""Agent-X Kernel Package.

Provides core domain models, state machines, workflow DAG execution,
events, and persistence abstractions.
"""

from agentx.kernel.events import (
    EventBus,
    EventType,
    HITLEscalationEvent,
    KernelEvent,
    MissionStateTransitionEvent,
    ResourceEvent,
    TaskStateTransitionEvent,
    ToolExecutionEvent,
    WorkflowMutatedEvent,
)
from agentx.kernel.models import (
    Goal,
    Mission,
    MissionState,
    SuccessCriteria,
    Task,
)
from agentx.kernel.persistence import (
    EntityNotFoundError,
    InMemoryStateStore,
    StateStore,
    StateStoreError,
    TaskLockError,
)
from agentx.kernel.state_machine import (
    InvalidStateTransitionError,
    MissionStateMachine,
    TaskStateMachine,
)
from agentx.kernel.workflow import (
    CyclicDependencyError,
    TaskNotFoundError,
    Workflow,
)
from agentx.kernel.workflow_runner import (
    TaskExecutionResult,
    WorkflowRunner,
)

__all__ = [
    # Models
    "Goal",
    "SuccessCriteria",
    "Task",
    "MissionState",
    "Mission",
    # State Machines & Errors
    "MissionStateMachine",
    "TaskStateMachine",
    "InvalidStateTransitionError",
    # Workflow
    "Workflow",
    "CyclicDependencyError",
    "TaskNotFoundError",
    "WorkflowRunner",
    "TaskExecutionResult",
    # Events
    "EventType",
    "KernelEvent",
    "MissionStateTransitionEvent",
    "TaskStateTransitionEvent",
    "WorkflowMutatedEvent",
    "HITLEscalationEvent",
    "ResourceEvent",
    "ToolExecutionEvent",
    "EventBus",
    # Persistence
    "StateStore",
    "InMemoryStateStore",
    "StateStoreError",
    "EntityNotFoundError",
    "TaskLockError",
]

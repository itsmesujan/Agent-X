"""Agent-X Kernel Deterministic State Machines for Missions and Tasks."""

from datetime import UTC, datetime

from agentx.kernel.events import MissionStateTransitionEvent, TaskStateTransitionEvent
from agentx.kernel.models import Mission, Task
from agentx_common.schemas import MissionStatus, TaskStatus


class InvalidStateTransitionError(Exception):
    """Raised when an illegal or unsupported state transition is attempted."""

    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        current_status: str,
        target_status: str,
        message: str | None = None,
    ) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.current_status = current_status
        self.target_status = target_status
        msg = (
            message
            or f"Invalid {entity_type} transition for '{entity_id}' from '{current_status}' to '{target_status}'"
        )
        super().__init__(msg)


class MissionStateMachine:
    """Deterministic, validated state machine for the 11-stage Mission lifecycle."""

    # Explicit transition graph
    VALID_TRANSITIONS: dict[MissionStatus, set[MissionStatus]] = {
        MissionStatus.DRAFT: {
            MissionStatus.PARSING_GOAL,
            MissionStatus.ABORTED,
        },
        MissionStatus.PARSING_GOAL: {
            MissionStatus.BUILDING_WORLD_MODEL,
            MissionStatus.FAILED,
            MissionStatus.ABORTED,
        },
        MissionStatus.BUILDING_WORLD_MODEL: {
            MissionStatus.PLANNING,
            MissionStatus.FAILED,
            MissionStatus.ABORTED,
        },
        MissionStatus.PLANNING: {
            MissionStatus.ALLOCATING_RESOURCES,
            MissionStatus.FAILED,
            MissionStatus.ABORTED,
        },
        MissionStatus.ALLOCATING_RESOURCES: {
            MissionStatus.READY,
            MissionStatus.FAILED,
            MissionStatus.ABORTED,
        },
        MissionStatus.READY: {
            MissionStatus.EXECUTING,
            MissionStatus.ABORTED,
        },
        MissionStatus.EXECUTING: {
            MissionStatus.PAUSED,
            MissionStatus.COMPLETED,
            MissionStatus.FAILED,
            MissionStatus.ABORTED,
        },
        MissionStatus.PAUSED: {
            MissionStatus.EXECUTING,
            MissionStatus.ABORTED,
        },
        # Terminal states have no outbound transitions
        MissionStatus.COMPLETED: set(),
        MissionStatus.FAILED: set(),
        MissionStatus.ABORTED: set(),
    }

    @classmethod
    def can_transition(cls, current: MissionStatus, target: MissionStatus) -> bool:
        """Check if transition from current to target status is valid."""
        return target in cls.VALID_TRANSITIONS.get(current, set())

    @classmethod
    def transition(
        cls,
        mission: Mission,
        target_status: MissionStatus,
        reason: str | None = None,
    ) -> MissionStateTransitionEvent:
        """Execute a state transition on a Mission, enforcing invariants and emitting an event."""
        current_status = mission.state.status

        if not cls.can_transition(current_status, target_status):
            raise InvalidStateTransitionError(
                entity_type="Mission",
                entity_id=mission.mission_id,
                current_status=current_status.value,
                target_status=target_status.value,
            )

        now = datetime.now(UTC)
        mission.state.previous_status = current_status
        mission.state.status = target_status
        mission.state.transition_count += 1
        mission.state.last_transition_at = now
        mission.updated_at = now

        if target_status == MissionStatus.COMPLETED:
            mission.completed_at = now
        elif target_status == MissionStatus.FAILED:
            mission.state.error_reason = reason

        return MissionStateTransitionEvent(
            mission_id=mission.mission_id,
            from_status=current_status,
            to_status=target_status,
            reason=reason,
            timestamp=now,
            payload={
                "transition_count": mission.state.transition_count,
                "completed_at": mission.completed_at.isoformat() if mission.completed_at else None,
            },
        )


class TaskStateMachine:
    """Deterministic, validated state machine for individual Task execution lifecycle."""

    VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
        TaskStatus.PENDING: {
            TaskStatus.READY,
            TaskStatus.SKIPPED,
            TaskStatus.PAUSED,
        },
        TaskStatus.READY: {
            TaskStatus.DISPATCHED,
            TaskStatus.RUNNING,
            TaskStatus.SKIPPED,
            TaskStatus.PAUSED,
        },
        TaskStatus.DISPATCHED: {
            TaskStatus.RUNNING,
            TaskStatus.FAILED,
            TaskStatus.PAUSED,
            TaskStatus.SKIPPED,
        },
        TaskStatus.RUNNING: {
            TaskStatus.VERIFYING,
            TaskStatus.VERIFIED,
            TaskStatus.FAILED,
            TaskStatus.PAUSED,
            TaskStatus.SKIPPED,
        },
        TaskStatus.VERIFYING: {
            TaskStatus.VERIFIED,
            TaskStatus.FAILED,
            TaskStatus.PAUSED,
            TaskStatus.SKIPPED,
        },
        TaskStatus.FAILED: {
            TaskStatus.READY,  # Re-queue on retry or recovery
            TaskStatus.SKIPPED,
            TaskStatus.PAUSED,
        },
        TaskStatus.PAUSED: {
            TaskStatus.PENDING,
            TaskStatus.READY,
            TaskStatus.RUNNING,
            TaskStatus.SKIPPED,
            TaskStatus.FAILED,
        },
        # Terminal states
        TaskStatus.VERIFIED: set(),
        TaskStatus.SKIPPED: set(),
    }

    @classmethod
    def can_transition(cls, current: TaskStatus, target: TaskStatus) -> bool:
        """Check if transition from current to target status is valid."""
        return target in cls.VALID_TRANSITIONS.get(current, set())

    @classmethod
    def transition(
        cls,
        task: Task,
        target_status: TaskStatus,
        worker_id: str | None = None,
        error_message: str | None = None,
    ) -> TaskStateTransitionEvent:
        """Execute a state transition on a Task, enforcing invariants and emitting an event."""
        current_status = task.status

        if not cls.can_transition(current_status, target_status):
            raise InvalidStateTransitionError(
                entity_type="Task",
                entity_id=task.task_id,
                current_status=current_status.value,
                target_status=target_status.value,
            )

        now = datetime.now(UTC)
        task.status = target_status

        if worker_id:
            task.locked_by_worker_id = worker_id

        if target_status == TaskStatus.RUNNING and task.started_at is None:
            task.started_at = now
        elif target_status in (TaskStatus.VERIFIED, TaskStatus.SKIPPED):
            task.completed_at = now
            task.locked_by_worker_id = None
        elif target_status == TaskStatus.FAILED:
            task.retry_count += 1
            task.error_message = error_message
            task.locked_by_worker_id = None

        return TaskStateTransitionEvent(
            mission_id=task.mission_id,
            task_id=task.task_id,
            from_status=current_status,
            to_status=target_status,
            retry_count=task.retry_count,
            worker_id=worker_id,
            error_message=error_message,
            timestamp=now,
            payload={
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            },
        )

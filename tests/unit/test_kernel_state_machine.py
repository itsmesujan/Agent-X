"""Unit tests for deterministic Mission and Task state machines."""

import pytest

from agentx.kernel.events import (
    EventType,
    MissionStateTransitionEvent,
    TaskStateTransitionEvent,
)
from agentx.kernel.models import Goal, Mission, Task
from agentx.kernel.state_machine import (
    InvalidStateTransitionError,
    MissionStateMachine,
    TaskStateMachine,
)
from agentx_common.schemas import AgentRole, MissionStatus, TaskStatus


def verify_mission_status(mission: Mission, expected: MissionStatus) -> None:
    assert mission.state.status == expected


def verify_task_status(task: Task, expected: TaskStatus) -> None:
    assert task.status == expected


def verify_mission_event(evt: MissionStateTransitionEvent, expected: MissionStatus) -> None:
    assert evt.to_status == expected


def verify_task_event(evt: TaskStateTransitionEvent, expected: TaskStatus) -> None:
    assert evt.to_status == expected


def verify_task_lease(task: Task, expected_worker: str | None) -> None:
    assert task.locked_by_worker_id == expected_worker


def verify_task_completed(task: Task) -> None:
    assert task.completed_at is not None


def verify_task_started(task: Task) -> None:
    assert task.started_at is not None


@pytest.fixture
def sample_mission() -> Mission:
    goal = Goal(
        goal_statement="Perform infrastructure audit",
        primary_objective="Scan IAM permissions",
    )
    return Mission(title="Audit Mission", goal=goal)


@pytest.fixture
def sample_task() -> Task:
    return Task(
        mission_id="msn_test",
        name="Scan IAM",
        description="Verify service account permissions",
        agent_role=AgentRole.DEVOPS,
    )


# --- Mission State Machine Tests ---


def test_mission_linear_happy_path(sample_mission: Mission) -> None:
    """Verify standard happy-path progression from DRAFT to COMPLETED."""
    verify_mission_status(sample_mission, MissionStatus.DRAFT)

    evt1 = MissionStateMachine.transition(sample_mission, MissionStatus.PARSING_GOAL)
    verify_mission_status(sample_mission, MissionStatus.PARSING_GOAL)
    assert evt1.event_type == EventType.MISSION_STATE_CHANGED
    assert evt1.from_status == MissionStatus.DRAFT
    verify_mission_event(evt1, MissionStatus.PARSING_GOAL)

    MissionStateMachine.transition(sample_mission, MissionStatus.BUILDING_WORLD_MODEL)
    verify_mission_status(sample_mission, MissionStatus.BUILDING_WORLD_MODEL)

    MissionStateMachine.transition(sample_mission, MissionStatus.PLANNING)
    verify_mission_status(sample_mission, MissionStatus.PLANNING)

    MissionStateMachine.transition(sample_mission, MissionStatus.ALLOCATING_RESOURCES)
    verify_mission_status(sample_mission, MissionStatus.ALLOCATING_RESOURCES)

    MissionStateMachine.transition(sample_mission, MissionStatus.READY)
    verify_mission_status(sample_mission, MissionStatus.READY)

    MissionStateMachine.transition(sample_mission, MissionStatus.EXECUTING)
    verify_mission_status(sample_mission, MissionStatus.EXECUTING)

    evt_done = MissionStateMachine.transition(sample_mission, MissionStatus.COMPLETED)
    verify_mission_status(sample_mission, MissionStatus.COMPLETED)
    assert sample_mission.completed_at is not None
    verify_mission_event(evt_done, MissionStatus.COMPLETED)


def test_mission_pause_and_resume(sample_mission: Mission) -> None:
    """Verify pausing and resuming during execution."""
    sample_mission.state.status = MissionStatus.EXECUTING

    MissionStateMachine.transition(
        sample_mission, MissionStatus.PAUSED, reason="Awaiting user confirmation"
    )
    verify_mission_status(sample_mission, MissionStatus.PAUSED)

    MissionStateMachine.transition(sample_mission, MissionStatus.EXECUTING)
    verify_mission_status(sample_mission, MissionStatus.EXECUTING)


def test_mission_failure_transition(sample_mission: Mission) -> None:
    """Verify failure transition records error reason."""
    sample_mission.state.status = MissionStatus.PLANNING

    evt = MissionStateMachine.transition(
        sample_mission, MissionStatus.FAILED, reason="Token budget depleted"
    )
    verify_mission_status(sample_mission, MissionStatus.FAILED)
    assert sample_mission.state.error_reason == "Token budget depleted"
    assert evt.reason == "Token budget depleted"


def test_mission_abort_transition(sample_mission: Mission) -> None:
    """Verify mission can be aborted from active states."""
    sample_mission.state.status = MissionStatus.EXECUTING
    MissionStateMachine.transition(sample_mission, MissionStatus.ABORTED, reason="User cancelled")
    verify_mission_status(sample_mission, MissionStatus.ABORTED)


def test_mission_illegal_transitions(sample_mission: Mission) -> None:
    """Verify all illegal transitions raise InvalidStateTransitionError."""
    # Cannot jump DRAFT -> EXECUTING
    with pytest.raises(InvalidStateTransitionError):
        MissionStateMachine.transition(sample_mission, MissionStatus.EXECUTING)

    # Cannot transition from terminal states
    sample_mission.state.status = MissionStatus.COMPLETED
    with pytest.raises(InvalidStateTransitionError):
        MissionStateMachine.transition(sample_mission, MissionStatus.EXECUTING)

    sample_mission.state.status = MissionStatus.FAILED
    with pytest.raises(InvalidStateTransitionError):
        MissionStateMachine.transition(sample_mission, MissionStatus.PLANNING)

    sample_mission.state.status = MissionStatus.ABORTED
    with pytest.raises(InvalidStateTransitionError):
        MissionStateMachine.transition(sample_mission, MissionStatus.READY)


# --- Task State Machine Tests ---


def test_task_linear_happy_path(sample_task: Task) -> None:
    """Verify standard happy-path task execution from PENDING to VERIFIED."""
    verify_task_status(sample_task, TaskStatus.PENDING)

    evt_ready = TaskStateMachine.transition(sample_task, TaskStatus.READY)
    verify_task_status(sample_task, TaskStatus.READY)
    verify_task_event(evt_ready, TaskStatus.READY)

    evt_disp = TaskStateMachine.transition(sample_task, TaskStatus.DISPATCHED)
    verify_task_status(sample_task, TaskStatus.DISPATCHED)
    verify_task_event(evt_disp, TaskStatus.DISPATCHED)

    evt_run = TaskStateMachine.transition(sample_task, TaskStatus.RUNNING, worker_id="worker_01")
    verify_task_status(sample_task, TaskStatus.RUNNING)
    verify_task_started(sample_task)
    verify_task_lease(sample_task, "worker_01")
    assert evt_run.worker_id == "worker_01"

    evt_ver = TaskStateMachine.transition(sample_task, TaskStatus.VERIFYING)
    verify_task_status(sample_task, TaskStatus.VERIFYING)
    verify_task_event(evt_ver, TaskStatus.VERIFYING)

    evt_done = TaskStateMachine.transition(sample_task, TaskStatus.VERIFIED)
    verify_task_status(sample_task, TaskStatus.VERIFIED)
    verify_task_completed(sample_task)
    verify_task_lease(sample_task, None)
    verify_task_event(evt_done, TaskStatus.VERIFIED)


def test_task_failure_and_retry(sample_task: Task) -> None:
    """Verify task failure increments retry count and allows transition to READY."""
    sample_task.status = TaskStatus.RUNNING

    evt_fail = TaskStateMachine.transition(
        sample_task, TaskStatus.FAILED, error_message="API connection timeout"
    )
    verify_task_status(sample_task, TaskStatus.FAILED)
    assert sample_task.retry_count == 1
    assert sample_task.error_message == "API connection timeout"
    verify_task_lease(sample_task, None)
    assert evt_fail.retry_count == 1

    # Retry transition back to READY
    TaskStateMachine.transition(sample_task, TaskStatus.READY)
    verify_task_status(sample_task, TaskStatus.READY)


def test_task_skip_transition(sample_task: Task) -> None:
    """Verify task can be skipped from PENDING, READY, or FAILED."""
    TaskStateMachine.transition(sample_task, TaskStatus.SKIPPED)
    verify_task_status(sample_task, TaskStatus.SKIPPED)
    verify_task_completed(sample_task)


def test_task_illegal_transitions(sample_task: Task) -> None:
    """Verify illegal task transitions raise InvalidStateTransitionError."""
    # Cannot jump PENDING -> RUNNING directly
    with pytest.raises(InvalidStateTransitionError):
        TaskStateMachine.transition(sample_task, TaskStatus.RUNNING)

    # Terminal state VERIFIED has no outbound transitions
    sample_task.status = TaskStatus.VERIFIED
    with pytest.raises(InvalidStateTransitionError):
        TaskStateMachine.transition(sample_task, TaskStatus.READY)

    # Terminal state SKIPPED has no outbound transitions
    sample_task.status = TaskStatus.SKIPPED
    with pytest.raises(InvalidStateTransitionError):
        TaskStateMachine.transition(sample_task, TaskStatus.RUNNING)

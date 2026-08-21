"""Unit tests for Kernel Persistence Abstraction and InMemoryStateStore."""

import pytest

from agentx.kernel.events import EventType, KernelEvent
from agentx.kernel.models import Goal, Mission, Task
from agentx.kernel.persistence import EntityNotFoundError, InMemoryStateStore
from agentx_common.schemas import AgentRole, MissionStatus, TaskStatus


@pytest.fixture
def store() -> InMemoryStateStore:
    return InMemoryStateStore()


def test_mission_crud(store: InMemoryStateStore) -> None:
    goal = Goal(
        goal_statement="Build test container",
        primary_objective="Compile dockerfile",
    )
    mission = Mission(title="Docker Build", goal=goal)

    store.save_mission(mission)
    fetched = store.get_mission(mission.mission_id)

    assert fetched is not None
    assert fetched.mission_id == mission.mission_id
    assert fetched.title == "Docker Build"
    assert fetched.state.status == MissionStatus.DRAFT

    all_missions = store.list_missions()
    assert len(all_missions) == 1


def test_task_crud(store: InMemoryStateStore) -> None:
    task = Task(
        task_id="task_test_01",
        mission_id="msn_100",
        name="Compile Code",
        description="Run tsc",
        agent_role=AgentRole.CODER,
    )

    store.save_task(task)
    fetched = store.get_task(mission_id="msn_100", task_id="task_test_01")

    assert fetched is not None
    assert fetched.task_id == "task_test_01"
    assert fetched.status == TaskStatus.PENDING

    tasks = store.list_tasks(mission_id="msn_100")
    assert len(tasks) == 1
    assert tasks[0].name == "Compile Code"


def test_task_lease_locking(store: InMemoryStateStore) -> None:
    task = Task(
        task_id="task_lock_01",
        mission_id="msn_200",
        name="Deploy Workload",
        description="Deploy Cloud Run",
        agent_role=AgentRole.DEVOPS,
    )
    store.save_task(task)

    # Worker 1 acquires lock
    assert store.acquire_task_lock("msn_200", "task_lock_01", "worker_1", lease_seconds=60)

    # Worker 2 attempts lock while active -> should be rejected
    assert not store.acquire_task_lock("msn_200", "task_lock_01", "worker_2", lease_seconds=60)

    # Worker 1 releases lock
    assert store.release_task_lock("msn_200", "task_lock_01", "worker_1")

    # Worker 2 can now acquire lock
    assert store.acquire_task_lock("msn_200", "task_lock_01", "worker_2", lease_seconds=60)


def test_task_lock_nonexistent_task_error(store: InMemoryStateStore) -> None:
    with pytest.raises(EntityNotFoundError):
        store.acquire_task_lock("msn_invalid", "task_invalid", "worker_1")


def test_event_recording(store: InMemoryStateStore) -> None:
    evt1 = KernelEvent(
        mission_id="msn_300",
        event_type=EventType.MISSION_CREATED,
        payload={"title": "Mission 300"},
    )
    evt2 = KernelEvent(
        mission_id="msn_300",
        event_type=EventType.MISSION_STATE_CHANGED,
        payload={"to_status": "PARSING_GOAL"},
    )

    store.record_event(evt1)
    store.record_event(evt2)

    events = store.get_events("msn_300")
    assert len(events) == 2
    assert events[0].event_type == EventType.MISSION_CREATED
    assert events[1].event_type == EventType.MISSION_STATE_CHANGED

"""Unit tests for Agent-X Dynamic Mutable Workflow Engine and Parallel Runner."""

import asyncio

import pytest

from agentx.kernel.events import EventBus, WorkflowMutatedEvent
from agentx.kernel.models import Task
from agentx.kernel.workflow import CyclicDependencyError, Workflow
from agentx.kernel.workflow_runner import TaskExecutionResult, WorkflowRunner
from agentx_common.schemas import AgentRole, TaskStatus


def make_task(
    task_id: str,
    mission_id: str = "msn_dyn_01",
    name: str | None = None,
    dependencies: list[str] | None = None,
    agent_role: AgentRole = AgentRole.CODER,
    status: TaskStatus = TaskStatus.PENDING,
) -> Task:
    return Task(
        task_id=task_id,
        mission_id=mission_id,
        name=name or f"Task {task_id}",
        description="Dynamic task description",
        agent_role=agent_role,
        status=status,
        dependencies=dependencies or [],
    )


def test_create_and_start_task() -> None:
    """Test dynamic CREATE TASK and START TASK operations."""
    events = EventBus()
    workflow = Workflow(mission_id="msn_dyn_01", event_bus=events)

    task: Task = workflow.create_task(
        name="Ingest Terraform",
        description="Read main.tf",
        agent_role=AgentRole.DEVOPS,
        task_id="t_dyn_01",
    )

    assert workflow.task_count == 1
    assert task.task_id == "t_dyn_01"
    assert task.status == TaskStatus.PENDING

    # Start task
    start_evt = workflow.start_task("t_dyn_01", worker_id="worker_alpha")
    current_status: TaskStatus = task.status
    assert current_status == TaskStatus.RUNNING
    assert task.locked_by_worker_id == "worker_alpha"
    assert task.started_at is not None
    assert start_evt.to_status == TaskStatus.RUNNING


def test_pause_and_resume_task() -> None:
    """Test PAUSE TASK and RESUME TASK operations."""
    events = EventBus()
    t1: Task = make_task("t1")
    workflow = Workflow(mission_id="msn_dyn_01", tasks=[t1], event_bus=events)

    workflow.start_task("t1")
    cur_status_1: TaskStatus = t1.status
    assert cur_status_1 == TaskStatus.RUNNING

    # Pause
    pause_evt = workflow.pause_task("t1", reason="Waiting for rate limit")
    cur_status_2: TaskStatus = t1.status
    assert cur_status_2 == TaskStatus.PAUSED
    assert pause_evt.to_status == TaskStatus.PAUSED

    # Resume
    resume_evt = workflow.resume_task("t1")
    cur_status_3: TaskStatus = t1.status
    assert cur_status_3 == TaskStatus.READY
    assert resume_evt.to_status == TaskStatus.READY


def test_cancel_task() -> None:
    """Test CANCEL TASK operation transitioning status to SKIPPED."""
    events = EventBus()
    t1: Task = make_task("t1")
    workflow = Workflow(mission_id="msn_dyn_01", tasks=[t1], event_bus=events)

    cancel_evt = workflow.cancel_task("t1", reason="User decided to skip")
    cur_status: TaskStatus = t1.status
    assert cur_status == TaskStatus.SKIPPED
    assert cancel_evt.to_status == TaskStatus.SKIPPED

    # Check WorkflowMutatedEvent emitted
    mut_events = [e for e in events.get_events() if isinstance(e, WorkflowMutatedEvent)]
    assert len(mut_events) == 1
    assert mut_events[0].mutation_type == "CANCEL_TASK"


def test_split_task_sequential() -> None:
    """Test splitting a task into a sequential chain of 3 subtasks."""
    events = EventBus()
    # A -> B -> C
    tA = make_task("tA")
    tB = make_task("tB", dependencies=["tA"])
    tC = make_task("tC", dependencies=["tB"])

    workflow = Workflow(mission_id="msn_dyn_01", tasks=[tA, tB, tC], event_bus=events)

    # Split B into B1 -> B2 -> B3
    s1 = make_task("tB1")
    s2 = make_task("tB2")
    s3 = make_task("tB3")

    workflow.split_task("tB", subtasks=[s1, s2, s3], sequential=True)

    assert workflow.task_count == 5  # tA, tB1, tB2, tB3, tC
    assert "tB" not in [t.task_id for t in workflow.get_all_tasks()]

    # Verify B1 depends on A
    assert workflow.get_task("tB1").dependencies == ["tA"]
    # Verify B2 depends on B1
    assert workflow.get_task("tB2").dependencies == ["tB1"]
    # Verify B3 depends on B2
    assert workflow.get_task("tB3").dependencies == ["tB2"]
    # Verify C depends on B3
    assert workflow.get_task("tC").dependencies == ["tB3"]


def test_split_task_parallel() -> None:
    """Test splitting a task into a parallel fan-out group of subtasks."""
    tA = make_task("tA")
    tB = make_task("tB", dependencies=["tA"])
    tC = make_task("tC", dependencies=["tB"])

    workflow = Workflow(mission_id="msn_dyn_01", tasks=[tA, tB, tC])

    p1 = make_task("tP1")
    p2 = make_task("tP2")

    workflow.split_task("tB", subtasks=[p1, p2], sequential=False)

    assert workflow.get_task("tP1").dependencies == ["tA"]
    assert workflow.get_task("tP2").dependencies == ["tA"]
    assert set(workflow.get_task("tC").dependencies) == {"tP1", "tP2"}


def test_merge_tasks() -> None:
    """Test combining two sequential tasks into one merged task."""
    events = EventBus()
    # A -> M1 -> M2 -> D
    tA = make_task("tA")
    tM1 = make_task("tM1", dependencies=["tA"])
    tM2 = make_task("tM2", dependencies=["tM1"])
    tD = make_task("tD", dependencies=["tM2"])

    workflow = Workflow(mission_id="msn_dyn_01", tasks=[tA, tM1, tM2, tD], event_bus=events)

    merged = make_task("tMerged")
    workflow.merge_tasks(["tM1", "tM2"], merged_task=merged)

    assert workflow.task_count == 3  # tA, tMerged, tD
    assert workflow.get_task("tMerged").dependencies == ["tA"]
    assert workflow.get_task("tD").dependencies == ["tMerged"]


def test_reorder_dependencies_and_cycle_prevention() -> None:
    """Test reordering task dependencies and catching cycles."""
    t1 = make_task("t1")
    t2 = make_task("t2")
    t3 = make_task("t3", dependencies=["t1"])

    workflow = Workflow(mission_id="msn_dyn_01", tasks=[t1, t2, t3])

    # Reorder t3 to depend on t2 instead of t1
    workflow.reorder_dependencies("t3", new_dependencies=["t2"])
    assert workflow.get_task("t3").dependencies == ["t2"]

    # Attempting to make t2 depend on t3 (cycle!) must raise CyclicDependencyError
    with pytest.raises(CyclicDependencyError):
        workflow.reorder_dependencies("t2", new_dependencies=["t3"])


def test_change_priority_agent_and_tool() -> None:
    """Test dynamic modifications to priority, agent role, and tools."""
    events = EventBus()
    task = make_task("t_mod", agent_role=AgentRole.CODER)
    workflow = Workflow(mission_id="msn_dyn_01", tasks=[task], event_bus=events)

    # 1. Change priority
    workflow.change_priority("t_mod", new_priority=95)
    assert task.inputs["priority"] == 95

    # 2. Change agent role
    orig_key = task.idempotency_key
    workflow.change_agent("t_mod", new_agent_role=AgentRole.ARCHITECT)
    assert task.agent_role == AgentRole.ARCHITECT
    assert task.idempotency_key != orig_key  # Recalculated!

    # 3. Change tools
    workflow.change_tools("t_mod", new_tools=["terraform_cli", "gcloud_cli"])
    assert task.inputs["tools"] == ["terraform_cli", "gcloud_cli"]


@pytest.mark.asyncio
async def test_parallel_workflow_execution() -> None:
    """Test concurrent parallel execution of diamond DAG (A -> B, C -> D)."""
    events = EventBus()

    # Diamond Topology:
    #      ┌─► B ─┐
    #   A ─┤      ├─► D
    #      └─► C ─┘
    tA = make_task("tA")
    tB = make_task("tB", dependencies=["tA"])
    tC = make_task("tC", dependencies=["tA"])
    tD = make_task("tD", dependencies=["tB", "tC"])

    workflow = Workflow(mission_id="msn_dyn_01", tasks=[tA, tB, tC, tD], event_bus=events)
    runner = WorkflowRunner(event_bus=events)

    execution_order: list[str] = []
    concurrency_highwater = 0
    currently_running = 0

    async def mock_task_handler(task: Task) -> TaskExecutionResult:
        nonlocal concurrency_highwater, currently_running
        currently_running += 1
        concurrency_highwater = max(concurrency_highwater, currently_running)

        # Simulate async work
        await asyncio.sleep(0.02)
        execution_order.append(task.task_id)

        currently_running -= 1
        return TaskExecutionResult(
            task_id=task.task_id,
            is_success=True,
            outputs={"result": f"Executed {task.name}"},
        )

    progress = await runner.run_workflow(
        workflow=workflow,
        task_handler=mock_task_handler,
        max_concurrency=4,
    )

    assert workflow.is_complete() is True
    assert progress["verified"] == 4
    assert progress["completion_percentage"] == 100.0

    # Verify execution order invariants:
    # tA must be first
    assert execution_order[0] == "tA"
    # tD must be last
    assert execution_order[-1] == "tD"
    # tB and tC ran in parallel in the middle
    assert set(execution_order[1:3]) == {"tB", "tC"}
    assert concurrency_highwater >= 2  # Proves parallel execution!

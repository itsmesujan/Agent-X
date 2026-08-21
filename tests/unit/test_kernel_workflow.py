"""Unit tests for Agent-X Workflow DAG engine."""

import pytest

from agentx.kernel.models import Task
from agentx.kernel.state_machine import TaskStateMachine
from agentx.kernel.workflow import (
    CyclicDependencyError,
    TaskNotFoundError,
    Workflow,
)
from agentx_common.schemas import AgentRole, TaskStatus


def create_task(task_id: str, name: str, dependencies: list[str] | None = None) -> Task:
    return Task(
        task_id=task_id,
        mission_id="msn_test_workflow",
        name=name,
        description=f"Description for {name}",
        agent_role=AgentRole.CODER,
        dependencies=dependencies or [],
    )


def test_workflow_topological_sort_diamond() -> None:
    r"""Diamond DAG:
        A
       / \
      B   C
       \ /
        D
    """
    t_a = create_task("task_a", "Init")
    t_b = create_task("task_b", "Build Backend", dependencies=["task_a"])
    t_c = create_task("task_c", "Build Frontend", dependencies=["task_a"])
    t_d = create_task("task_d", "Integration Test", dependencies=["task_b", "task_c"])

    wf = Workflow(mission_id="msn_test_workflow", tasks=[t_a, t_b, t_c, t_d])
    order = wf.validate_dag()

    assert order[0] == "task_a"
    assert order[-1] == "task_d"
    assert set(order[1:3]) == {"task_b", "task_c"}
    assert wf.task_count == 4


def test_workflow_cyclic_dependency_detection() -> None:
    """Cycle: A -> B -> C -> A"""
    t_a = create_task("task_a", "Task A", dependencies=["task_c"])
    t_b = create_task("task_b", "Task B", dependencies=["task_a"])
    t_c = create_task("task_c", "Task C", dependencies=["task_b"])

    with pytest.raises(CyclicDependencyError):
        Workflow(mission_id="msn_test_workflow", tasks=[t_a, t_b, t_c])


def test_workflow_missing_dependency_error() -> None:
    """Task depends on non-existent task ID."""
    t_a = create_task("task_a", "Task A", dependencies=["task_ghost"])

    with pytest.raises(TaskNotFoundError):
        Workflow(mission_id="msn_test_workflow", tasks=[t_a])


def test_workflow_ready_tasks_progression() -> None:
    """Verify ready tasks unlock as upstream tasks become VERIFIED."""
    t1 = create_task("t1", "Stage 1")
    t2 = create_task("t2", "Stage 2", dependencies=["t1"])

    wf = Workflow(mission_id="msn_test_workflow", tasks=[t1, t2])

    # Initial state: only t1 is ready
    ready = wf.get_ready_tasks()
    assert len(ready) == 1
    assert ready[0].task_id == "t1"
    assert t1.status == TaskStatus.READY

    # Progress t1 to VERIFIED
    TaskStateMachine.transition(t1, TaskStatus.DISPATCHED)
    TaskStateMachine.transition(t1, TaskStatus.RUNNING)
    TaskStateMachine.transition(t1, TaskStatus.VERIFYING)
    TaskStateMachine.transition(t1, TaskStatus.VERIFIED)

    # Now t2 should be ready
    ready_after = wf.get_ready_tasks()
    assert len(ready_after) == 1
    assert ready_after[0].task_id == "t2"
    assert t2.status == TaskStatus.READY


def test_workflow_dynamic_subtree_injection() -> None:
    """Verify live DAG surgery when a task fails and requires repair tasks."""
    t1 = create_task("t1", "Scaffold Project")
    t2 = create_task("t2", "Compile Typescript", dependencies=["t1"])
    t3 = create_task("t3", "Deploy Artifact", dependencies=["t2"])

    wf = Workflow(mission_id="msn_test_workflow", tasks=[t1, t2, t3])

    # t1 is verified, t2 failed
    t1.status = TaskStatus.VERIFIED
    t2.status = TaskStatus.FAILED

    # Create repair tasks
    r1 = create_task("r1", "Diagnose Type Errors", dependencies=[])
    r2 = create_task("r2", "Patch Missing Types", dependencies=["r1"])

    mutation_evt = wf.inject_repair_subtree(
        failed_task_id="t2",
        repair_tasks=[r1, r2],
        reason="Self-healing TypeScript compilation error",
    )

    assert mutation_evt.mutation_type == "INJECT_SUBTREE"
    assert "r1" in mutation_evt.affected_task_ids
    assert "r2" in mutation_evt.affected_task_ids

    # Verify dependency wiring
    assert r1.dependencies == ["t1"]  # r1 inherited t2's dependency
    assert t3.dependencies == ["r2"]  # t3 now depends on the repair end node
    assert wf.task_count == 5

    # Verify DAG remains valid
    order = wf.validate_dag()
    assert order.index("t1") < order.index("r1") < order.index("r2") < order.index("t3")


def test_workflow_progress_and_completion() -> None:
    t1 = create_task("t1", "Task 1")
    t2 = create_task("t2", "Task 2", dependencies=["t1"])

    wf = Workflow(mission_id="msn_test_workflow", tasks=[t1, t2])
    assert not wf.is_complete()

    progress = wf.get_progress()
    assert progress["total_tasks"] == 2
    assert progress["completion_percentage"] == 0.0

    t1.status = TaskStatus.VERIFIED
    t2.status = TaskStatus.SKIPPED

    assert wf.is_complete()
    progress_done = wf.get_progress()
    assert progress_done["completion_percentage"] == 100.0
    assert progress_done["verified"] == 1
    assert progress_done["skipped"] == 1

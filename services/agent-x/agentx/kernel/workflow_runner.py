"""Agent-X Parallel Workflow Execution Runner."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agentx.kernel.events import EventBus
from agentx.kernel.models import Task
from agentx.kernel.state_machine import TaskStateMachine
from agentx.kernel.workflow import Workflow
from agentx_common.schemas import TaskStatus


class TaskExecutionResult(BaseModel):
    """Result payload produced by an executed task."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    is_success: bool
    outputs: dict[str, Any] = Field(default_factory=dict)
    evidence_uri: str | None = None
    error_message: str | None = None


class WorkflowRunner:
    """Coordinates concurrent parallel task execution and dynamic dependency resolution."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.event_bus = event_bus or EventBus()

    async def execute_task_wrapper(
        self,
        workflow: Workflow,
        task: Task,
        task_handler: Callable[[Task], Awaitable[TaskExecutionResult]],
        worker_id: str,
    ) -> TaskExecutionResult:
        """Executes a single task, manages state transitions, and emits events."""
        # 1. Transition to RUNNING
        start_evt = workflow.start_task(task.task_id, worker_id=worker_id)
        self.event_bus.publish(start_evt)

        try:
            result = await task_handler(task)

            if result.is_success:
                task.outputs = result.outputs
                task.evidence_uri = result.evidence_uri

                # Transition RUNNING -> VERIFIED
                verified_evt = TaskStateMachine.transition(task, TaskStatus.VERIFIED)
                self.event_bus.publish(verified_evt)
            else:
                fail_evt = TaskStateMachine.transition(
                    task, TaskStatus.FAILED, error_message=result.error_message
                )
                self.event_bus.publish(fail_evt)

            return result

        except Exception as e:
            fail_evt = TaskStateMachine.transition(task, TaskStatus.FAILED, error_message=str(e))
            self.event_bus.publish(fail_evt)
            return TaskExecutionResult(
                task_id=task.task_id,
                is_success=False,
                error_message=str(e),
            )

    async def run_workflow(
        self,
        workflow: Workflow,
        task_handler: Callable[[Task], Awaitable[TaskExecutionResult]],
        max_concurrency: int = 4,
        poll_interval_seconds: float = 0.01,
    ) -> dict[str, Any]:
        """Execute the workflow DAG with dynamic parallel concurrency."""
        active_futures: dict[asyncio.Task[TaskExecutionResult], str] = {}
        semaphore = asyncio.Semaphore(max_concurrency)

        async def worker_slot(t: Task, w_id: str) -> TaskExecutionResult:
            async with semaphore:
                return await self.execute_task_wrapper(workflow, t, task_handler, worker_id=w_id)

        worker_counter = 0

        while not workflow.is_complete() and not workflow.has_unrecoverable_failures():
            # 1. Discover newly ready tasks
            ready_tasks = workflow.get_ready_tasks()

            for r_task in ready_tasks:
                worker_counter += 1
                w_id = f"worker_{worker_counter:03d}"
                # Schedule task execution in background
                fut = asyncio.create_task(worker_slot(r_task, w_id))
                active_futures[fut] = r_task.task_id

            if not active_futures:
                # No tasks currently running and none ready -> deadlocked or done
                break

            # Wait for at least one active task to complete
            done, _ = await asyncio.wait(active_futures.keys(), return_when=asyncio.FIRST_COMPLETED)

            for finished_fut in done:
                _ = active_futures.pop(finished_fut)
                # Ensure exceptions are raised / handled
                _ = finished_fut.result()

        return workflow.get_progress()

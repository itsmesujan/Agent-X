"""Agent-X Kernel Workflow DAG Engine with Live Dynamic Mutation and Execution."""

from collections import deque
from typing import Any
from uuid import uuid4

from agentx.kernel.events import (
    EventBus,
    EventType,
    TaskStateTransitionEvent,
    WorkflowMutatedEvent,
)
from agentx.kernel.models import Task
from agentx.kernel.state_machine import TaskStateMachine
from agentx_common.schemas import AgentRole, TaskStatus, VerificationLevel


class CyclicDependencyError(Exception):
    """Raised when a circular dependency is detected in the Task DAG."""

    def __init__(self, message: str = "Circular dependency detected in workflow DAG") -> None:
        super().__init__(message)


class TaskNotFoundError(Exception):
    """Raised when a referenced task does not exist in the workflow."""

    def __init__(self, task_id: str) -> None:
        super().__init__(f"Task with ID '{task_id}' was not found in workflow")


class Workflow:
    """Manages the dynamic, mutable Directed Acyclic Graph (DAG) of tasks for a Mission."""

    def __init__(
        self,
        mission_id: str,
        tasks: list[Task] | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.mission_id = mission_id
        self._tasks: dict[str, Task] = {}
        self.event_bus: EventBus = event_bus or EventBus()

        if tasks:
            for task in tasks:
                self.add_task(task, validate=False)
            self.validate_dag()

    @property
    def task_count(self) -> int:
        return len(self._tasks)

    # --- GRAPH TOPOLOGY & CORE ACCESS ---

    def add_task(self, task: Task, validate: bool = True) -> None:
        """Add a task node to the workflow and maintain graph adjacency."""
        if task.task_id in self._tasks:
            raise ValueError(f"Task with ID '{task.task_id}' already exists in workflow")

        if task.mission_id != self.mission_id:
            raise ValueError(
                f"Task mission_id '{task.mission_id}' does not match workflow mission_id '{self.mission_id}'"
            )

        self._tasks[task.task_id] = task

        # Update dependent_children on parent tasks
        for parent_id in task.dependencies:
            if parent_id in self._tasks:
                parent_task = self._tasks[parent_id]
                if task.task_id not in parent_task.dependent_children:
                    parent_task.dependent_children.append(task.task_id)

        # Update dependent_children on this task if children were added earlier
        for existing_id, existing_task in self._tasks.items():
            if task.task_id in existing_task.dependencies:
                if existing_id not in task.dependent_children:
                    task.dependent_children.append(existing_id)

        if validate:
            self.validate_dag()

    def remove_task(self, task_id: str, validate: bool = True) -> Task:
        """Remove a task from the workflow and detach all edge pointers."""
        task = self.get_task(task_id)

        # Remove from parents' dependent_children
        for parent_id in task.dependencies:
            if parent_id in self._tasks:
                if task_id in self._tasks[parent_id].dependent_children:
                    self._tasks[parent_id].dependent_children.remove(task_id)

        # Remove from children's dependencies
        for child_id in task.dependent_children:
            if child_id in self._tasks:
                if task_id in self._tasks[child_id].dependencies:
                    self._tasks[child_id].dependencies.remove(task_id)

        del self._tasks[task_id]

        if validate:
            self.validate_dag()
        return task

    def get_task(self, task_id: str) -> Task:
        """Retrieve a task by ID or raise TaskNotFoundError."""
        if task_id not in self._tasks:
            raise TaskNotFoundError(task_id)
        return self._tasks[task_id]

    def get_all_tasks(self) -> list[Task]:
        """Return all tasks in the workflow."""
        return list(self._tasks.values())

    def get_dependencies(self, task_id: str) -> list[Task]:
        """Retrieve parent prerequisite tasks for a given task."""
        task = self.get_task(task_id)
        return [self.get_task(dep_id) for dep_id in task.dependencies]

    def get_downstream_dependents(self, task_id: str) -> list[Task]:
        """Retrieve child dependent tasks for a given task."""
        task = self.get_task(task_id)
        return [self.get_task(child_id) for child_id in task.dependent_children]

    def validate_dag(self) -> list[str]:
        """Validate that the task graph is a valid DAG using Kahn's algorithm.

        Returns topological sort ordering of task IDs.
        Raises CyclicDependencyError if cycles are present.
        """
        for task_id, task in self._tasks.items():
            for dep_id in task.dependencies:
                if dep_id not in self._tasks:
                    raise TaskNotFoundError(
                        f"Task '{task_id}' references non-existent dependency '{dep_id}'"
                    )

        in_degree: dict[str, int] = {t_id: len(t.dependencies) for t_id, t in self._tasks.items()}
        queue: deque[str] = deque([t_id for t_id, deg in in_degree.items() if deg == 0])
        topological_order: list[str] = []

        while queue:
            node_id = queue.popleft()
            topological_order.append(node_id)

            for child_id in self._tasks[node_id].dependent_children:
                in_degree[child_id] -= 1
                if in_degree[child_id] == 0:
                    queue.append(child_id)

        if len(topological_order) != len(self._tasks):
            unresolved = [t_id for t_id, deg in in_degree.items() if deg > 0]
            raise CyclicDependencyError(
                f"Circular dependency detected involving tasks: {', '.join(unresolved)}"
            )

        return topological_order

    def get_ready_tasks(self) -> list[Task]:
        """Find all tasks whose dependencies are all VERIFIED and are ready to execute."""
        ready: list[Task] = []

        for task in self._tasks.values():
            if task.status in (TaskStatus.PENDING, TaskStatus.READY):
                all_deps_satisfied = True
                for dep_id in task.dependencies:
                    dep_task = self._tasks[dep_id]
                    if dep_task.status not in (TaskStatus.VERIFIED, TaskStatus.SKIPPED):
                        all_deps_satisfied = False
                        break

                if all_deps_satisfied:
                    if task.status == TaskStatus.PENDING:
                        event = TaskStateMachine.transition(task, TaskStatus.READY)
                        self.event_bus.publish(event)
                    ready.append(task)

        return ready

    # --- 1. CREATE TASK ---

    def create_task(
        self,
        name: str,
        description: str,
        agent_role: AgentRole,
        dependencies: list[str] | None = None,
        expected_outputs: list[str] | None = None,
        allocated_tokens: int = 25000,
        timeout_seconds: int = 300,
        verification_level: VerificationLevel = VerificationLevel.LEVEL_3_ARTIFACT,
        inputs: dict[str, Any] | None = None,
        task_id: str | None = None,
    ) -> Task:
        """Dynamically create and insert a new task node into the live workflow."""
        task = Task(
            task_id=task_id or f"task_{uuid4().hex[:8]}",
            mission_id=self.mission_id,
            name=name,
            description=description,
            agent_role=agent_role,
            status=TaskStatus.PENDING,
            dependencies=dependencies or [],
            expected_outputs=expected_outputs or [],
            allocated_tokens=allocated_tokens,
            timeout_seconds=timeout_seconds,
            verification_level=verification_level,
            inputs=inputs or {},
        )
        self.add_task(task, validate=True)

        event = WorkflowMutatedEvent(
            mission_id=self.mission_id,
            event_type=EventType.WORKFLOW_MUTATED,
            mutation_type="CREATE_TASK",
            affected_task_ids=[task.task_id],
            reason=f"Dynamically created task '{task.name}'",
            payload={"task_id": task.task_id, "agent_role": agent_role.value},
        )
        self.event_bus.publish(event)
        return task

    # --- 2. START TASK ---

    def start_task(self, task_id: str, worker_id: str | None = None) -> TaskStateTransitionEvent:
        """Transition a task to RUNNING state."""
        task = self.get_task(task_id)
        if task.status == TaskStatus.PENDING:
            TaskStateMachine.transition(task, TaskStatus.READY)
        event = TaskStateMachine.transition(task, TaskStatus.RUNNING, worker_id=worker_id)
        self.event_bus.publish(event)
        return event

    # --- 3. PAUSE TASK ---

    def pause_task(
        self, task_id: str, reason: str = "Paused by user/recovery"
    ) -> TaskStateTransitionEvent:
        """Pause a task during execution."""
        task = self.get_task(task_id)
        event = TaskStateMachine.transition(task, TaskStatus.PAUSED)
        self.event_bus.publish(event)
        return event

    # --- 4. RESUME TASK ---

    def resume_task(self, task_id: str) -> TaskStateTransitionEvent:
        """Resume a paused task back to READY or RUNNING."""
        task = self.get_task(task_id)
        # Check dependencies
        all_satisfied = all(
            self._tasks[dep].status in (TaskStatus.VERIFIED, TaskStatus.SKIPPED)
            for dep in task.dependencies
        )
        target = TaskStatus.READY if all_satisfied else TaskStatus.PENDING
        event = TaskStateMachine.transition(task, target)
        self.event_bus.publish(event)
        return event

    # --- 5. CANCEL TASK ---

    def cancel_task(
        self, task_id: str, reason: str = "Cancelled by user"
    ) -> TaskStateTransitionEvent:
        """Cancel a task by transitioning to SKIPPED."""
        task = self.get_task(task_id)
        event = TaskStateMachine.transition(task, TaskStatus.SKIPPED)
        self.event_bus.publish(event)

        mutation_evt = WorkflowMutatedEvent(
            mission_id=self.mission_id,
            event_type=EventType.WORKFLOW_MUTATED,
            mutation_type="CANCEL_TASK",
            affected_task_ids=[task_id],
            reason=reason,
            payload={"task_id": task_id},
        )
        self.event_bus.publish(mutation_evt)
        return event

    # --- 6. SPLIT TASK ---

    def split_task(
        self,
        task_id: str,
        subtasks: list[Task],
        sequential: bool = True,
        reason: str = "Split task into smaller subtasks",
    ) -> WorkflowMutatedEvent:  # noqa: C901
        """Divide an existing task into a sequence or parallel group of subtasks."""
        if not subtasks:
            raise ValueError("Cannot split task into empty subtasks list")

        orig_task = self.get_task(task_id)
        orig_deps = list(orig_task.dependencies)
        orig_children = list(orig_task.dependent_children)

        # 1. Remove original task
        self.remove_task(task_id, validate=False)

        # 2. Add all subtasks
        for st in subtasks:
            self.add_task(st, validate=False)

        # 3. Rewire edges
        if sequential:
            # First subtask gets orig_deps
            for dep in orig_deps:
                if dep not in subtasks[0].dependencies:
                    subtasks[0].dependencies.append(dep)
                    self._tasks[dep].dependent_children.append(subtasks[0].task_id)

            # Chain subtasks sequentially
            for i in range(len(subtasks) - 1):
                cur, nxt = subtasks[i], subtasks[i + 1]
                if cur.task_id not in nxt.dependencies:
                    nxt.dependencies.append(cur.task_id)
                if nxt.task_id not in cur.dependent_children:
                    cur.dependent_children.append(nxt.task_id)

            # Last subtask connects to orig_children
            last_st = subtasks[-1]
            for child_id in orig_children:
                child = self._tasks[child_id]
                if last_st.task_id not in child.dependencies:
                    child.dependencies.append(last_st.task_id)
                if child_id not in last_st.dependent_children:
                    last_st.dependent_children.append(child_id)
        else:
            # Parallel split: all subtasks inherit orig_deps and connect to orig_children
            for st in subtasks:
                for dep in orig_deps:
                    if dep not in st.dependencies:
                        st.dependencies.append(dep)
                        self._tasks[dep].dependent_children.append(st.task_id)
                for child_id in orig_children:
                    child = self._tasks[child_id]
                    if st.task_id not in child.dependencies:
                        child.dependencies.append(st.task_id)
                    if child_id not in st.dependent_children:
                        st.dependent_children.append(child_id)

        # Validate DAG acyclicity
        self.validate_dag()

        affected_ids = [task_id] + [st.task_id for st in subtasks] + orig_children
        event = WorkflowMutatedEvent(
            mission_id=self.mission_id,
            event_type=EventType.WORKFLOW_MUTATED,
            mutation_type="SPLIT_TASK",
            affected_task_ids=affected_ids,
            reason=reason,
            payload={"original_task_id": task_id, "subtask_count": len(subtasks)},
        )
        self.event_bus.publish(event)
        return event

    # --- 7. MERGE TASKS ---

    def merge_tasks(
        self,
        task_ids: list[str],
        merged_task: Task,
        reason: str = "Merged tasks into consolidated task",
    ) -> WorkflowMutatedEvent:  # noqa: C901
        """Combine multiple tasks into a single consolidated task node."""
        if len(task_ids) < 2:
            raise ValueError("Merging requires at least 2 task IDs")

        merged_task_set = set(task_ids)
        external_deps: set[str] = set()
        external_children: set[str] = set()

        for t_id in task_ids:
            t = self.get_task(t_id)
            for dep in t.dependencies:
                if dep not in merged_task_set:
                    external_deps.add(dep)
            for dep_child_id in t.dependent_children:
                if dep_child_id not in merged_task_set:
                    external_children.add(dep_child_id)

        # Remove old tasks
        for t_id in task_ids:
            self.remove_task(t_id, validate=False)

        # Configure merged task dependencies
        merged_task.dependencies = sorted(external_deps)
        self.add_task(merged_task, validate=False)

        # Rewire children to depend on merged_task
        for child_id in external_children:
            child_task = self._tasks[child_id]
            if merged_task.task_id not in child_task.dependencies:
                child_task.dependencies.append(merged_task.task_id)
            if child_id not in merged_task.dependent_children:
                merged_task.dependent_children.append(child_id)

        self.validate_dag()

        affected_ids = task_ids + [merged_task.task_id]
        event = WorkflowMutatedEvent(
            mission_id=self.mission_id,
            event_type=EventType.WORKFLOW_MUTATED,
            mutation_type="MERGE_TASKS",
            affected_task_ids=affected_ids,
            reason=reason,
            payload={"merged_task_id": merged_task.task_id, "source_task_ids": task_ids},
        )
        self.event_bus.publish(event)
        return event

    # --- 8. REORDER TASK / DEPENDENCIES ---

    def reorder_dependencies(
        self,
        task_id: str,
        new_dependencies: list[str],
        reason: str = "Reordered task dependencies",
    ) -> WorkflowMutatedEvent:  # noqa: C901
        """Update a task's prerequisite dependencies and validate DAG integrity."""
        task = self.get_task(task_id)
        old_deps = list(task.dependencies)

        # Remove from old parents' dependent_children
        for old_dep in old_deps:
            if old_dep in self._tasks and task_id in self._tasks[old_dep].dependent_children:
                self._tasks[old_dep].dependent_children.remove(task_id)

        # Add to new parents' dependent_children
        for new_dep in new_dependencies:
            if new_dep not in self._tasks:
                raise TaskNotFoundError(f"Prerequisite '{new_dep}' does not exist in workflow")
            if task_id not in self._tasks[new_dep].dependent_children:
                self._tasks[new_dep].dependent_children.append(task_id)

        task.dependencies = list(new_dependencies)

        # Enforce DAG Acyclicity
        try:
            self.validate_dag()
        except CyclicDependencyError as e:
            # Revert on cycle
            task.dependencies = old_deps
            for new_dep in new_dependencies:
                if task_id in self._tasks[new_dep].dependent_children:
                    self._tasks[new_dep].dependent_children.remove(task_id)
            for old_dep in old_deps:
                if task_id not in self._tasks[old_dep].dependent_children:
                    self._tasks[old_dep].dependent_children.append(task_id)
            raise e

        event = WorkflowMutatedEvent(
            mission_id=self.mission_id,
            event_type=EventType.WORKFLOW_MUTATED,
            mutation_type="REORDER_TASK",
            affected_task_ids=[task_id],
            reason=reason,
            payload={"task_id": task_id, "old_deps": old_deps, "new_deps": new_dependencies},
        )
        self.event_bus.publish(event)
        return event

    # --- 9. CHANGE PRIORITY ---

    def change_priority(
        self,
        task_id: str,
        new_priority: int,
        reason: str = "Priority modified",
    ) -> WorkflowMutatedEvent:
        """Change a task's scheduling priority dynamically."""
        task = self.get_task(task_id)
        old_priority = task.inputs.get("priority", 50)
        task.inputs["priority"] = new_priority

        event = WorkflowMutatedEvent(
            mission_id=self.mission_id,
            event_type=EventType.WORKFLOW_MUTATED,
            mutation_type="CHANGE_PRIORITY",
            affected_task_ids=[task_id],
            reason=reason,
            payload={
                "task_id": task_id,
                "old_priority": old_priority,
                "new_priority": new_priority,
            },
        )
        self.event_bus.publish(event)
        return event

    # --- 10. CHANGE AGENT ---

    def change_agent(
        self,
        task_id: str,
        new_agent_role: AgentRole,
        reason: str = "Reassigned agent persona",
    ) -> WorkflowMutatedEvent:
        """Reassign a task to a different agent persona and recompute idempotency key."""
        task = self.get_task(task_id)
        old_role = task.agent_role
        task.agent_role = new_agent_role
        task.idempotency_key = task.compute_idempotency_key()

        event = WorkflowMutatedEvent(
            mission_id=self.mission_id,
            event_type=EventType.WORKFLOW_MUTATED,
            mutation_type="CHANGE_AGENT",
            affected_task_ids=[task_id],
            reason=reason,
            payload={
                "task_id": task_id,
                "old_role": old_role.value,
                "new_role": new_agent_role.value,
            },
        )
        self.event_bus.publish(event)
        return event

    # --- 11. CHANGE TOOL ---

    def change_tools(
        self,
        task_id: str,
        new_tools: list[str],
        reason: str = "Assigned tools updated",
    ) -> WorkflowMutatedEvent:
        """Update the tool inventory allocated to a task."""
        task = self.get_task(task_id)
        old_tools = task.inputs.get("tools", [])
        task.inputs["tools"] = list(new_tools)

        event = WorkflowMutatedEvent(
            mission_id=self.mission_id,
            event_type=EventType.WORKFLOW_MUTATED,
            mutation_type="CHANGE_TOOL",
            affected_task_ids=[task_id],
            reason=reason,
            payload={"task_id": task_id, "old_tools": old_tools, "new_tools": new_tools},
        )
        self.event_bus.publish(event)
        return event

    # --- REPAIR SUBTREE INJECTION ---

    def inject_repair_subtree(
        self,
        failed_task_id: str,
        repair_tasks: list[Task],
        reason: str,
    ) -> WorkflowMutatedEvent:
        """Dynamically injects self-healing repair tasks into the live DAG."""
        failed_task = self.get_task(failed_task_id)
        downstream_ids = list(failed_task.dependent_children)

        for task in repair_tasks:
            self.add_task(task, validate=False)

        if repair_tasks:
            first_repair = repair_tasks[0]
            for dep in failed_task.dependencies:
                if dep not in first_repair.dependencies:
                    first_repair.dependencies.append(dep)
                    self._tasks[dep].dependent_children.append(first_repair.task_id)

            last_repair = repair_tasks[-1]
            for down_id in downstream_ids:
                down_task = self._tasks[down_id]
                if failed_task_id in down_task.dependencies:
                    down_task.dependencies.remove(failed_task_id)
                if last_repair.task_id not in down_task.dependencies:
                    down_task.dependencies.append(last_repair.task_id)
                    last_repair.dependent_children.append(down_id)

            failed_task.dependent_children.clear()

        self.validate_dag()

        affected_ids = [t.task_id for t in repair_tasks] + downstream_ids + [failed_task_id]
        event = WorkflowMutatedEvent(
            mission_id=self.mission_id,
            event_type=EventType.WORKFLOW_MUTATED,
            mutation_type="INJECT_SUBTREE",
            affected_task_ids=affected_ids,
            reason=reason,
            payload={"failed_task_id": failed_task_id, "repair_task_count": len(repair_tasks)},
        )
        self.event_bus.publish(event)
        return event

    # --- STATUS & PROGRESS ---

    def is_complete(self) -> bool:
        """Returns True if every task in the workflow is in a terminal state (VERIFIED or SKIPPED)."""
        if not self._tasks:
            return False
        return all(
            t.status in (TaskStatus.VERIFIED, TaskStatus.SKIPPED) for t in self._tasks.values()
        )

    def has_unrecoverable_failures(self) -> bool:
        """Returns True if any task has permanently failed (max retries exceeded)."""
        return any(
            t.status == TaskStatus.FAILED and t.retry_count >= t.max_retries
            for t in self._tasks.values()
        )

    def get_progress(self) -> dict[str, Any]:
        """Compute aggregate progress metrics across the workflow."""
        total = len(self._tasks)
        if total == 0:
            return {"total": 0, "verified": 0, "percentage": 0.0}

        counts: dict[str, int] = {status.value: 0 for status in TaskStatus}
        for task in self._tasks.values():
            counts[task.status.value] += 1

        verified_count = counts[TaskStatus.VERIFIED.value] + counts[TaskStatus.SKIPPED.value]
        pct = round((verified_count / total) * 100.0, 2)

        return {
            "total_tasks": total,
            "verified": counts[TaskStatus.VERIFIED.value],
            "skipped": counts[TaskStatus.SKIPPED.value],
            "running": counts[TaskStatus.RUNNING.value],
            "dispatched": counts[TaskStatus.DISPATCHED.value],
            "ready": counts[TaskStatus.READY.value],
            "pending": counts[TaskStatus.PENDING.value],
            "failed": counts[TaskStatus.FAILED.value],
            "paused": counts[TaskStatus.PAUSED.value],
            "completion_percentage": pct,
        }

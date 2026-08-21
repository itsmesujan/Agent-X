"""Agent-X Goal Drift Detector and Automated DAG Remediation Controller."""

from typing import Any

from agentx.drift.evaluator import RelevanceEvaluator
from agentx.drift.schemas import (
    DriftEvaluationResult,
    DriftRemediationAction,
    DriftRemediationRecord,
    DriftSeverity,
    TaskRelevanceReport,
)
from agentx.kernel.events import EventBus, EventType, KernelEvent
from agentx.kernel.models import Mission, Task
from agentx.kernel.workflow import Workflow
from agentx_common.schemas import TaskStatus


class GoalDriftDetector:
    """Continuously evaluates active tasks against mission intent and executes remediation actions."""

    def __init__(
        self,
        event_bus: EventBus | None = None,
        drift_threshold: float = 0.60,
        critical_threshold: float = 0.20,
    ) -> None:
        self.event_bus = event_bus
        self.evaluator = RelevanceEvaluator(
            drift_threshold=drift_threshold,
            critical_threshold=critical_threshold,
        )
        self._remediations: dict[str, DriftRemediationRecord] = {}

    # --- 1. EVALUATE WORKFLOW ---

    def evaluate_workflow(
        self,
        mission: Mission,
        workflow: Workflow,
    ) -> DriftEvaluationResult:
        """Evaluates all non-terminal tasks in a workflow against the original mission intent."""
        tasks = workflow.get_all_tasks()
        reports: list[TaskRelevanceReport] = []
        recommended: dict[str, DriftRemediationAction] = {}
        drifted_count = 0

        for t in tasks:
            # Skip already completed or cancelled tasks
            if t.status in (TaskStatus.VERIFIED, TaskStatus.SKIPPED):
                continue

            rep = self.evaluator.evaluate_task(t, mission)
            reports.append(rep)

            if rep.severity == DriftSeverity.CRITICAL_DRIFT:
                drifted_count += 1
                recommended[t.task_id] = DriftRemediationAction.CANCEL
            elif rep.severity == DriftSeverity.MODERATE_DRIFT:
                drifted_count += 1
                recommended[t.task_id] = DriftRemediationAction.PAUSE

        avg_score = (
            round(sum(r.relevance_score for r in reports) / len(reports), 4) if reports else 1.0
        )

        result = DriftEvaluationResult(
            mission_id=mission.mission_id,
            overall_drift_score=avg_score,
            task_reports=reports,
            drifted_task_count=drifted_count,
            recommended_remediations=recommended,
        )

        if drifted_count > 0 and self.event_bus:
            self.event_bus.publish(
                KernelEvent(
                    mission_id=mission.mission_id,
                    event_type=EventType.GOAL_DRIFT_DETECTED,
                    payload={
                        "drifted_count": drifted_count,
                        "overall_score": avg_score,
                        "recommendations": {k: v.value for k, v in recommended.items()},
                    },
                )
            )

        return result

    # --- 2. REMEDIATE DRIFT ---

    def remediate_drift(
        self,
        mission: Mission,
        workflow: Workflow,
        task_id: str,
        action: DriftRemediationAction,
        replacement_task: Task | None = None,
        reason: str = "",
    ) -> DriftRemediationRecord:
        """Applies a goal drift remediation action (FLAG, PAUSE, CANCEL, REPLACE, REPRIORITIZE) to the live DAG."""
        task = workflow.get_task(task_id)
        remediation_reason = reason or f"Goal drift remediation: {action.value}"
        details: dict[str, Any] = {"task_id": task_id, "action": action.value}

        match action:
            case DriftRemediationAction.FLAG:
                task.inputs["goal_drift_flagged"] = True
                details["status"] = "FLAGGED"

            case DriftRemediationAction.PAUSE:
                workflow.pause_task(task_id, reason=remediation_reason)
                details["status"] = "PAUSED"

            case DriftRemediationAction.CANCEL:
                workflow.cancel_task(task_id, reason=remediation_reason)
                details["status"] = "SKIPPED"

            case DriftRemediationAction.REPLACE:
                workflow.cancel_task(task_id, reason=f"Replaced due to drift: {remediation_reason}")
                if replacement_task:
                    # Inherit dependencies
                    replacement_task.dependencies = list(task.dependencies)
                    workflow.add_task(replacement_task, validate=True)
                    details["replacement_task_id"] = replacement_task.task_id
                details["status"] = "REPLACED"

            case DriftRemediationAction.REPRIORITIZE:
                # Lower token budget and mark priority 1 (low)
                task.allocated_tokens = max(5000, task.allocated_tokens // 2)
                task.inputs["priority"] = 1
                workflow.change_priority(task_id, new_priority=1, reason=remediation_reason)
                details["status"] = "REPRIORITIZED"
                details["new_priority"] = 1

        record = DriftRemediationRecord(
            mission_id=mission.mission_id,
            task_id=task_id,
            action=action,
            reason=remediation_reason,
            details=details,
        )
        self._remediations[record.remediation_id] = record

        if self.event_bus:
            self.event_bus.publish(
                KernelEvent(
                    mission_id=mission.mission_id,
                    event_type=EventType.GOAL_DRIFT_REMEDIATED,
                    payload={
                        "remediation_id": record.remediation_id,
                        "task_id": task_id,
                        "action": action.value,
                        "details": details,
                    },
                )
            )

        return record

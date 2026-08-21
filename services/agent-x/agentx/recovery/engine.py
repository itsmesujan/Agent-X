"""Agent-X Automated Recovery & Self-Healing Engine."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from agentx.kernel.events import EventBus, EventType, KernelEvent
from agentx.kernel.models import Mission, Task
from agentx.kernel.workflow import Workflow
from agentx.recovery.classifier import ErrorClassifier
from agentx.recovery.schemas import (
    FailureCategory,
    FailureDiagnostic,
    HITLEscalation,
    RecoveryAction,
    RecoveryStrategyType,
)
from agentx.resource_brain.brain import ResourceBrain
from agentx_common.schemas import AgentRole, MissionStatus, TaskStatus


class RecoveryEngine:
    """Orchestrates diagnostic classification, recovery strategy selection, self-healing application, and HITL escalations."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.event_bus = event_bus
        self._diagnostics: dict[str, FailureDiagnostic] = {}
        self._actions: dict[str, RecoveryAction] = {}
        self._hitl_escalations: dict[str, HITLEscalation] = {}

    # --- 1. DIAGNOSE FAILURE ---

    def diagnose_failure(
        self,
        task: Task,
        error: Exception | str,
        stack_trace: str | None = None,
    ) -> FailureDiagnostic:
        """Classifies task runtime failure into one of the 9 Error Taxonomy categories."""
        category, err_type = ErrorClassifier.classify(error)
        err_msg = str(error)

        is_recoverable = True
        if task.retry_count >= task.max_retries:
            is_recoverable = False
        elif category == FailureCategory.PERMISSION and "401" in err_msg:
            # Unrecoverable without human credential provision
            is_recoverable = False

        diagnostic = FailureDiagnostic(
            task_id=task.task_id,
            mission_id=task.mission_id,
            category=category,
            error_message=err_msg,
            error_type=err_type,
            stack_trace=stack_trace,
            retry_count=task.retry_count,
            max_retries=task.max_retries,
            is_recoverable=is_recoverable,
        )

        self._diagnostics[diagnostic.diagnostic_id] = diagnostic

        if self.event_bus:
            self.event_bus.publish(
                KernelEvent(
                    mission_id=task.mission_id,
                    event_type=EventType.FAILURE_DIAGNOSED,
                    payload={
                        "diagnostic_id": diagnostic.diagnostic_id,
                        "task_id": task.task_id,
                        "category": diagnostic.category.value,
                        "error_message": diagnostic.error_message,
                        "is_recoverable": diagnostic.is_recoverable,
                    },
                )
            )

        return diagnostic

    # --- 2. SELECT RECOVERY STRATEGY ---

    def select_strategy(
        self,
        diagnostic: FailureDiagnostic,
        task: Task,
        context: dict[str, Any] | None = None,
    ) -> RecoveryAction:
        """Selects the optimal recovery strategy across the 9 available self-healing strategies."""
        ctx = context or {}

        # 1. If retries exhausted or non-recoverable, escalate to Human-in-the-Loop
        if not diagnostic.is_recoverable or diagnostic.retry_count >= diagnostic.max_retries:
            return self._create_action(
                strategy=RecoveryStrategyType.HUMAN_APPROVAL,
                diagnostic=diagnostic,
                task=task,
                parameters={
                    "reason": "Max retries exceeded or unrecoverable error boundary reached",
                    "suggested_actions": [
                        "Inspect task failure logs in Mission Control",
                        "Provide valid IAM credentials or API keys",
                        "Override task inputs or mark task as resolved",
                    ],
                },
                reasoning=f"Failure category {diagnostic.category.value} exhausted retries ({diagnostic.retry_count}/{diagnostic.max_retries}).",
            )

        # 2. Strategy routing by failure category
        match diagnostic.category:
            case FailureCategory.TRANSIENT:
                if diagnostic.retry_count == 0:
                    return self._create_action(
                        strategy=RecoveryStrategyType.RETRY,
                        diagnostic=diagnostic,
                        task=task,
                        parameters={},
                        reasoning="Initial transient failure; attempting immediate retry.",
                    )
                backoff_sec = round(2.0**diagnostic.retry_count * 1.5 + 0.5, 2)
                return self._create_action(
                    strategy=RecoveryStrategyType.BACKOFF,
                    diagnostic=diagnostic,
                    task=task,
                    parameters={"backoff_seconds": backoff_sec},
                    reasoning=f"Transient network/rate-limit error; applying exponential backoff ({backoff_sec}s).",
                )

            case FailureCategory.TOOL:
                alt_tool = ctx.get("alternative_tool")
                if alt_tool:
                    return self._create_action(
                        strategy=RecoveryStrategyType.ALTERNATIVE_TOOL,
                        diagnostic=diagnostic,
                        task=task,
                        parameters={"alternative_tool": alt_tool},
                        reasoning=f"Tool failed; routing task to fallback tool '{alt_tool}'.",
                    )
                return self._create_action(
                    strategy=RecoveryStrategyType.WORKFLOW_MUTATION,
                    diagnostic=diagnostic,
                    task=task,
                    parameters={
                        "inject_prerequisite_task": {
                            "name": f"Repair Tool: {task.name}",
                            "description": "Fix or reinstall tool dependencies",
                            "agent_role": AgentRole.DEVOPS.value,
                        }
                    },
                    reasoning="Tool unavailable; mutating workflow to inject tool repair prerequisite.",
                )

            case FailureCategory.DATA:
                return self._create_action(
                    strategy=RecoveryStrategyType.TASK_MODIFICATION,
                    diagnostic=diagnostic,
                    task=task,
                    parameters={"sanitize_inputs": True, "strict_schema": True},
                    reasoning="Schema/payload validation error; modifying task inputs with sanitization.",
                )

            case FailureCategory.RESOURCE:
                return self._create_action(
                    strategy=RecoveryStrategyType.RESOURCE_REALLOCATION,
                    diagnostic=diagnostic,
                    task=task,
                    parameters={"additional_tokens": 50000, "additional_usd": 1.00},
                    reasoning="Budget/resource quota exceeded; requesting resource reallocation from ResourceBrain.",
                )

            case FailureCategory.PERMISSION:
                return self._create_action(
                    strategy=RecoveryStrategyType.HUMAN_APPROVAL,
                    diagnostic=diagnostic,
                    task=task,
                    parameters={
                        "suggested_actions": [
                            "Grant IAM secretAccessor role in GCP",
                            "Update .env or Secret Manager token",
                        ]
                    },
                    reasoning="Permission denied; requires human credential/IAM approval.",
                )

            case FailureCategory.LOGIC:
                return self._create_action(
                    strategy=RecoveryStrategyType.TASK_MODIFICATION,
                    diagnostic=diagnostic,
                    task=task,
                    parameters={"injected_error_context": diagnostic.error_message},
                    reasoning="Assertion or logic failure; modifying task prompt with diagnostic context.",
                )

            case FailureCategory.MODEL:
                alt_agent = ctx.get("alternative_agent", AgentRole.CODER.value)
                return self._create_action(
                    strategy=RecoveryStrategyType.ALTERNATIVE_AGENT,
                    diagnostic=diagnostic,
                    task=task,
                    parameters={"alternative_agent": alt_agent},
                    reasoning=f"Model reasoning failure; routing to alternative agent '{alt_agent}'.",
                )

            case FailureCategory.ENVIRONMENT:
                return self._create_action(
                    strategy=RecoveryStrategyType.WORKFLOW_MUTATION,
                    diagnostic=diagnostic,
                    task=task,
                    parameters={
                        "inject_prerequisite_task": {
                            "name": "Install Environment Dependencies",
                            "description": "Execute pip/npm dependency installation",
                            "agent_role": AgentRole.DEVOPS.value,
                        }
                    },
                    reasoning="Environment dependency missing; mutating workflow to inject installer task.",
                )

            case FailureCategory.UNKNOWN | _:
                return self._create_action(
                    strategy=RecoveryStrategyType.REPLANNING,
                    diagnostic=diagnostic,
                    task=task,
                    parameters={"replan_branch": True},
                    reasoning="Unclassified failure; triggering strategy replanning.",
                )

    def _create_action(
        self,
        strategy: RecoveryStrategyType,
        diagnostic: FailureDiagnostic,
        task: Task,
        parameters: dict[str, Any],
        reasoning: str,
    ) -> RecoveryAction:
        action = RecoveryAction(
            strategy=strategy,
            diagnostic_id=diagnostic.diagnostic_id,
            target_task_id=task.task_id,
            mission_id=task.mission_id,
            parameters=parameters,
            reasoning=reasoning,
        )
        self._actions[action.action_id] = action
        return action

    # --- 3. APPLY RECOVERY ---

    def apply_recovery(
        self,
        action: RecoveryAction,
        task: Task,
        workflow: Workflow | None = None,
        resource_brain: ResourceBrain | None = None,
        mission: Mission | None = None,
    ) -> bool:
        """Applies the recovery action, mutates tasks/workflows, and publishes observable events."""
        action.status = "APPLIED"
        action.applied_at = datetime.now(UTC)

        match action.strategy:
            case RecoveryStrategyType.RETRY | RecoveryStrategyType.BACKOFF:
                task.retry_count += 1
                task.status = TaskStatus.READY

            case RecoveryStrategyType.ALTERNATIVE_TOOL:
                new_tool = action.parameters.get("alternative_tool", "")
                if workflow and new_tool:
                    workflow.change_tools(task.task_id, [new_tool])
                else:
                    task.inputs["tools"] = [new_tool]
                    task.retry_count += 1
                    task.status = TaskStatus.READY

            case RecoveryStrategyType.ALTERNATIVE_AGENT:
                new_agent = action.parameters.get("alternative_agent", AgentRole.CODER.value)
                if workflow:
                    workflow.change_agent(task.task_id, AgentRole(new_agent))
                else:
                    task.agent_role = AgentRole(new_agent)
                    task.retry_count += 1
                    task.status = TaskStatus.READY

            case RecoveryStrategyType.TASK_MODIFICATION:
                task.inputs.update(action.parameters)
                task.retry_count += 1
                task.status = TaskStatus.READY

            case RecoveryStrategyType.RESOURCE_REALLOCATION:
                add_tokens = action.parameters.get("additional_tokens", 50000)
                add_usd = action.parameters.get("additional_usd", 1.00)
                if resource_brain:
                    resource_brain.reallocate_budget(
                        from_task_id="system_reserve",
                        to_task_id=task.task_id,
                        usd_amount=add_usd,
                        tokens=add_tokens,
                        reason=action.reasoning,
                    )
                task.allocated_tokens += add_tokens
                task.retry_count += 1
                task.status = TaskStatus.READY

            case RecoveryStrategyType.WORKFLOW_MUTATION:
                inject_cfg = action.parameters.get("inject_prerequisite_task")
                if workflow and inject_cfg:
                    new_task_id = f"task_fix_{uuid4().hex[:6]}"
                    workflow.create_task(
                        task_id=new_task_id,
                        name=inject_cfg.get("name", "Fix Prerequisite"),
                        description=inject_cfg.get("description", "Automated fix prerequisite"),
                        agent_role=AgentRole(inject_cfg.get("agent_role", AgentRole.DEVOPS.value)),
                        dependencies=task.dependencies.copy(),
                    )
                    # Link injected task as dependency for the failing task
                    task.dependencies.append(new_task_id)
                task.status = TaskStatus.PENDING

            case RecoveryStrategyType.REPLANNING:
                if mission:
                    mission.state.status = MissionStatus.PLANNING

            case RecoveryStrategyType.HUMAN_APPROVAL:
                escalation = HITLEscalation(
                    mission_id=task.mission_id,
                    task_id=task.task_id,
                    error_category=FailureCategory.PERMISSION,
                    diagnosis=action.reasoning,
                    attempted_strategies=[action.strategy.value],
                    suggested_human_actions=action.parameters.get("suggested_actions", []),
                )
                self._hitl_escalations[escalation.escalation_id] = escalation
                if mission:
                    mission.state.status = MissionStatus.PAUSED

                if self.event_bus:
                    self.event_bus.publish(
                        KernelEvent(
                            mission_id=task.mission_id,
                            event_type=EventType.HITL_ESCALATION,
                            payload={
                                "escalation_id": escalation.escalation_id,
                                "task_id": task.task_id,
                                "diagnosis": escalation.diagnosis,
                                "suggested_actions": escalation.suggested_human_actions,
                            },
                        )
                    )

        # Publish observable RECOVERY_APPLIED event
        if self.event_bus:
            self.event_bus.publish(
                KernelEvent(
                    mission_id=task.mission_id,
                    event_type=EventType.RECOVERY_APPLIED,
                    payload={
                        "action_id": action.action_id,
                        "task_id": task.task_id,
                        "strategy": action.strategy.value,
                        "reasoning": action.reasoning,
                        "parameters": action.parameters,
                    },
                )
            )

        return True

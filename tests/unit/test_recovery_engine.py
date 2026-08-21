"""Unit and Failure Injection Tests for Agent-X Recovery Engine."""

from agentx.kernel.events import EventBus, EventType, KernelEvent
from agentx.kernel.models import Goal, Mission, MissionState, Task
from agentx.kernel.workflow import Workflow
from agentx.recovery import (
    ErrorClassifier,
    FailureCategory,
    RecoveryEngine,
    RecoveryStrategyType,
)
from agentx.resource_brain.brain import ResourceBrain
from agentx_common.schemas import AgentRole, MissionBudget, MissionStatus, TaskStatus


def make_test_task(
    task_id: str = "task_rec_01", retry_count: int = 0, max_retries: int = 3
) -> Task:
    return Task(
        task_id=task_id,
        mission_id="msn_rec_01",
        name="Test Deploy Service",
        description="Deploy Cloud Run service",
        agent_role=AgentRole.DEVOPS,
        status=TaskStatus.RUNNING,
        retry_count=retry_count,
        max_retries=max_retries,
        timeout_seconds=300,
        allocated_tokens=50000,
    )


def test_error_classifier_all_nine_categories() -> None:
    """Verify ErrorClassifier correctly maps error signals across all 9 failure categories."""
    assert (
        ErrorClassifier.classify(TimeoutError("Connection timed out after 30s"))[0]
        == FailureCategory.TRANSIENT
    )
    assert ErrorClassifier.classify("503 Service Unavailable")[0] == FailureCategory.TRANSIENT
    assert (
        ErrorClassifier.classify("ToolExecutionError: tool failed with code 1")[0]
        == FailureCategory.TOOL
    )
    assert (
        ErrorClassifier.classify("ValidationError: extra inputs are not permitted")[0]
        == FailureCategory.DATA
    )
    assert (
        ErrorClassifier.classify("BudgetExhaustedError: token budget exceeded")[0]
        == FailureCategory.RESOURCE
    )
    assert (
        ErrorClassifier.classify("PermissionError: 403 Forbidden on GCP Secret Manager")[0]
        == FailureCategory.PERMISSION
    )
    assert (
        ErrorClassifier.classify("AssertionError: test failed on expected value")[0]
        == FailureCategory.LOGIC
    )
    assert (
        ErrorClassifier.classify("PromptInjectionError: safety filter triggered")[0]
        == FailureCategory.MODEL
    )
    assert (
        ErrorClassifier.classify("ModuleNotFoundError: No module named 'google.genai'")[0]
        == FailureCategory.ENVIRONMENT
    )
    assert (
        ErrorClassifier.classify("Some completely obscure unhandled exception")[0]
        == FailureCategory.UNKNOWN
    )


def test_failure_injection_transient_retry_and_backoff() -> None:
    """Test retry on first transient failure and exponential backoff on subsequent failures."""
    event_bus = EventBus()
    events: list[KernelEvent] = []
    event_bus.subscribe_all(lambda e: events.append(e))

    engine = RecoveryEngine(event_bus=event_bus)
    task = make_test_task(retry_count=0)

    # 1. First transient failure -> RETRY
    diag1 = engine.diagnose_failure(task, TimeoutError("Read timeout"))
    assert diag1.category == FailureCategory.TRANSIENT
    action1 = engine.select_strategy(diag1, task)
    assert action1.strategy == RecoveryStrategyType.RETRY

    engine.apply_recovery(action1, task)
    assert task.retry_count == 1
    assert task.status == TaskStatus.READY

    # 2. Second transient failure -> BACKOFF
    diag2 = engine.diagnose_failure(task, "429 Too Many Requests")
    action2 = engine.select_strategy(diag2, task)
    assert action2.strategy == RecoveryStrategyType.BACKOFF
    assert action2.parameters["backoff_seconds"] > 0

    engine.apply_recovery(action2, task)
    assert task.retry_count == 2

    # Verify observable events emitted
    assert any(e.event_type == EventType.FAILURE_DIAGNOSED for e in events)
    assert any(e.event_type == EventType.RECOVERY_APPLIED for e in events)


def test_failure_injection_alternative_tool_and_agent() -> None:
    """Test switching to an alternative tool and alternative agent."""
    engine = RecoveryEngine()
    workflow = Workflow(mission_id="msn_rec_01")
    task = make_test_task()
    workflow.create_task(
        task_id=task.task_id,
        name=task.name,
        description=task.description,
        agent_role=task.agent_role,
    )

    # 1. Tool failure -> Alternative Tool
    diag_tool = engine.diagnose_failure(task, "ToolExecutionError: chrome-browser tool crashed")
    action_tool = engine.select_strategy(
        diag_tool, task, context={"alternative_tool": "web_research"}
    )
    assert action_tool.strategy == RecoveryStrategyType.ALTERNATIVE_TOOL

    engine.apply_recovery(action_tool, task, workflow=workflow)
    assert workflow.get_task(task.task_id).inputs["tools"] == ["web_research"]

    # 2. Model failure -> Alternative Agent
    task.retry_count = 1
    diag_model = engine.diagnose_failure(task, "PromptInjectionError: safety filter triggered")
    action_agent = engine.select_strategy(
        diag_model, task, context={"alternative_agent": AgentRole.CODER.value}
    )
    assert action_agent.strategy == RecoveryStrategyType.ALTERNATIVE_AGENT

    engine.apply_recovery(action_agent, task, workflow=workflow)
    assert workflow.get_task(task.task_id).agent_role == AgentRole.CODER


def test_failure_injection_task_modification_and_resource_reallocation() -> None:
    """Test modifying task parameters and reallocating tokens/budget from ResourceBrain."""
    engine = RecoveryEngine()
    resource_brain = ResourceBrain(
        mission_id="msn_rec_01",
        budget=MissionBudget(max_usd_limit=20.0, max_total_tokens=2_000_000),
    )

    task = make_test_task()

    # 1. Data failure -> Task Modification (sanitize inputs)
    diag_data = engine.diagnose_failure(task, "ValidationError: malformed payload")
    action_data = engine.select_strategy(diag_data, task)
    assert action_data.strategy == RecoveryStrategyType.TASK_MODIFICATION

    engine.apply_recovery(action_data, task)
    assert task.inputs.get("sanitize_inputs") is True

    # 2. Resource failure -> Resource Reallocation
    orig_tokens = task.allocated_tokens
    diag_res = engine.diagnose_failure(task, "BudgetExhaustedError: token budget exceeded")
    action_res = engine.select_strategy(diag_res, task)
    assert action_res.strategy == RecoveryStrategyType.RESOURCE_REALLOCATION

    engine.apply_recovery(action_res, task, resource_brain=resource_brain)
    assert task.allocated_tokens == orig_tokens + 50000


def test_failure_injection_workflow_mutation_injects_setup_task() -> None:
    """Test dynamic DAG mutation injecting a prerequisite dependency install task on Environment failure."""
    engine = RecoveryEngine()
    workflow = Workflow(mission_id="msn_rec_01")
    task = make_test_task()
    workflow.create_task(
        task_id=task.task_id,
        name=task.name,
        description=task.description,
        agent_role=task.agent_role,
    )

    diag_env = engine.diagnose_failure(task, "ModuleNotFoundError: No module named 'fastapi'")
    assert diag_env.category == FailureCategory.ENVIRONMENT

    action_env = engine.select_strategy(diag_env, task)
    assert action_env.strategy == RecoveryStrategyType.WORKFLOW_MUTATION

    engine.apply_recovery(action_env, task, workflow=workflow)

    # Verify a new task was dynamically injected into workflow
    assert len(workflow.get_all_tasks()) == 2
    injected_task_id = task.dependencies[-1]
    injected = workflow.get_task(injected_task_id)
    assert injected.name == "Install Environment Dependencies"
    assert injected.agent_role == AgentRole.DEVOPS


def test_failure_injection_replanning_and_hitl_escalation() -> None:
    """Test replanning and Human-in-the-Loop escalation when retries are exhausted or permission denied."""
    event_bus = EventBus()
    events: list[KernelEvent] = []
    event_bus.subscribe_all(lambda e: events.append(e))

    engine = RecoveryEngine(event_bus=event_bus)
    mission = Mission(
        mission_id="msn_rec_01",
        title="Recovery Mission",
        goal=Goal(
            goal_statement="Execute high risk task",
            primary_objective="Execute task",
        ),
        state=MissionState(status=MissionStatus.EXECUTING),
    )

    # 1. Unknown failure -> REPLANNING
    task = make_test_task(retry_count=0)
    diag_unknown = engine.diagnose_failure(task, "Mysterious unexplained failure")
    action_replan = engine.select_strategy(diag_unknown, task)
    assert action_replan.strategy == RecoveryStrategyType.REPLANNING

    engine.apply_recovery(action_replan, task, mission=mission)
    assert mission.state.status == MissionStatus.PLANNING

    # 2. Permission failure / Max retries exhausted -> HUMAN_APPROVAL
    task_exhausted = make_test_task(retry_count=3, max_retries=3)
    mission.state.status = MissionStatus.EXECUTING

    diag_perm = engine.diagnose_failure(
        task_exhausted, "PermissionError: 401 Unauthorized access denied"
    )
    action_hitl = engine.select_strategy(diag_perm, task_exhausted)
    assert action_hitl.strategy == RecoveryStrategyType.HUMAN_APPROVAL

    engine.apply_recovery(action_hitl, task_exhausted, mission=mission)
    assert mission.state.status == MissionStatus.PAUSED
    assert any(e.event_type == EventType.HITL_ESCALATION for e in events)

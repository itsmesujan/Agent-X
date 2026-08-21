"""Unit and API integration tests for the Agent-X Failure Center and Mission Timeline."""

import pytest
from fastapi.testclient import TestClient

from agentx.api.state import state_manager
from agentx.kernel.events import EventBus
from agentx.kernel.models import Task
from agentx.main import app
from agentx.recovery.engine import RecoveryEngine
from agentx.recovery.schemas import FailureCategory, RecoveryStrategyType
from agentx_common.schemas import AgentRole, TaskStatus


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def recovery_engine(event_bus: EventBus) -> RecoveryEngine:
    return RecoveryEngine(event_bus=event_bus)


def test_failure_center_error_classification_and_diagnosis(
    recovery_engine: RecoveryEngine,
) -> None:
    """Verify diagnostic classification across taxonomy categories."""
    mission_id = "msn_failure_test_001"
    task = Task(
        task_id="task_fail_001",
        mission_id=mission_id,
        name="Fetch OpenAPI Schema",
        description="Download schema from remote gateway",
        agent_role=AgentRole.CODER,
        status=TaskStatus.RUNNING,
    )

    # 1. Simulate a transient network timeout
    err = TimeoutError("Connection timed out after 30.0s")
    diag = recovery_engine.diagnose_failure(task=task, error=err)

    assert diag.category == FailureCategory.TRANSIENT
    assert "Connection timed out" in diag.error_message
    assert diag.is_recoverable is True
    assert diag.task_id == task.task_id

    # 2. Select strategy
    action = recovery_engine.select_strategy(diagnostic=diag, task=task)
    assert action.strategy in (RecoveryStrategyType.RETRY, RecoveryStrategyType.BACKOFF)
    assert action.status == "PROPOSED"


def test_failure_center_tool_replacement_and_resource_grant(
    recovery_engine: RecoveryEngine,
) -> None:
    """Verify alternative tool replacement and resource reallocation self-healing actions."""
    mission_id = "msn_failure_test_002"
    task = Task(
        task_id="task_tool_fail",
        mission_id=mission_id,
        name="Execute Data Transformation",
        description="Run pandas dataframe cleaner",
        agent_role=AgentRole.TESTER,
        inputs={"tools": ["broken_data_cleaner"]},
        status=TaskStatus.RUNNING,
    )

    # Simulate tool crash error
    err = RuntimeError("Tool failed: 'broken_data_cleaner' returned exit code 127")
    diag = recovery_engine.diagnose_failure(task=task, error=err)
    assert diag.category == FailureCategory.TOOL

    # Select alternative tool strategy
    action = recovery_engine.select_strategy(
        diagnostic=diag,
        task=task,
        context={"alternative_tool": "mock_data_analysis"},
    )
    assert action.strategy == RecoveryStrategyType.ALTERNATIVE_TOOL
    assert action.parameters.get("alternative_tool") == "mock_data_analysis"

    # Apply recovery
    applied = recovery_engine.apply_recovery(action=action, task=task)
    assert applied is True
    assert action.status == "APPLIED"
    assert task.inputs["tools"] == ["mock_data_analysis"]
    assert task.retry_count == 1
    assert task.status == TaskStatus.READY


def test_api_failure_center_endpoints_and_timeline() -> None:
    """Verify FastAPI GET /missions/{id}/failures returns all 7 attributes and the timeline."""
    client = TestClient(app)
    headers = {"Authorization": "Bearer dev-token-auditor"}

    # 1. Create a test mission with workflow and recovery engine
    mission = state_manager.create_mission(
        title="Failure Center Integration Verification",
        goal_statement="Diagnose errors and render timeline.",
    )
    mission_id = mission.mission_id

    wf = state_manager.get_workflow(mission_id)
    rec_engine = state_manager.get_recovery_engine(mission_id)
    assert wf is not None
    assert rec_engine is not None

    # Create task in workflow
    task = wf.create_task(
        task_id="task_audit_fail",
        name="Run Security Audit",
        description="Execute automated SAIF security scan",
        agent_role=AgentRole.AUDITOR,
    )
    task.status = TaskStatus.RUNNING

    # Diagnose a resource error
    err = MemoryError("Out of memory: Token budget exceeded 100,000 boundary")
    diag = rec_engine.diagnose_failure(task=task, error=err)
    action = rec_engine.select_strategy(diagnostic=diag, task=task)
    rec_engine.apply_recovery(action=action, task=task)

    # 2. Call GET /missions/{id}/failures
    resp = client.get(f"/api/v1/missions/{mission_id}/failures", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["mission_id"] == mission_id
    assert data["summary"]["total_failures"] == 1
    assert data["summary"]["healed_count"] >= 1
    assert len(data["failures"]) == 1

    f = data["failures"][0]
    # Check all 7 attributes
    assert "Out of memory: Token budget exceeded" in f["failure"]
    assert f["classification"] == "RESOURCE"
    assert f["affected_task_id"] == "task_audit_fail"
    assert f["affected_task_name"] == "Run Security Audit"
    assert f["assigned_agent"] == "AUDITOR"
    assert f["recovery_strategy"] == "RESOURCE_REALLOCATION"
    assert f["replacement"] == "N/A - Re-executing with existing tools"
    assert "+50,000 tokens" in f["additional_resources"]
    assert f["result"] in ("APPLIED", "RECOVERED")

    # Check Timeline
    timeline = data["timeline"]
    assert len(timeline) >= 2
    types = [evt["event_type"] for evt in timeline]
    assert "MISSION_CREATED" in types
    assert "FAILURE_DIAGNOSED" in types
    assert "RECOVERY_APPLIED" in types

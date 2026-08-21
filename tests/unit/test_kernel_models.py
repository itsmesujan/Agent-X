"""Unit tests for Agent-X Kernel domain models."""

from agentx.kernel.models import (
    Goal,
    Mission,
    MissionState,
    SuccessCriteria,
    Task,
)
from agentx_common.schemas import (
    AgentRole,
    MissionStatus,
    TaskStatus,
    VerificationLevel,
)


def test_success_criteria_defaults() -> None:
    crit = SuccessCriteria(description="Response latency must be under 200ms")
    assert crit.criteria_id.startswith("crit_")
    assert crit.verification_level == VerificationLevel.LEVEL_4_SEMANTIC
    assert not crit.is_satisfied
    assert crit.expected_metric is None
    assert crit.evidence_uri is None


def test_goal_validation_and_defaults() -> None:
    goal = Goal(
        goal_statement="Deploy new cloud function for telemetry",
        primary_objective="Create Terraform definition and deploy Cloud Run service",
        constraints={"max_usd": 2.0},
    )
    assert len(goal.deliverables) == 1
    assert goal.deliverables[0] == "verified_mission_outcome"
    assert goal.constraints["max_usd"] == 2.0


def test_task_idempotency_key_auto_generation() -> None:
    task1 = Task(
        mission_id="msn_123",
        name="Build Container",
        description="Build Docker image",
        agent_role=AgentRole.CODER,
        inputs={"tag": "v1.0.0"},
    )
    task2 = Task(
        mission_id="msn_123",
        name="Build Container",
        description="Build Docker image",
        agent_role=AgentRole.CODER,
        inputs={"tag": "v1.0.0"},
    )
    assert task1.idempotency_key != ""
    assert task1.idempotency_key == task2.idempotency_key


def test_task_pending_properties() -> None:
    task = Task(
        mission_id="msn_123",
        name="Audit Secrets",
        description="Check repo for secret leaks",
        agent_role=AgentRole.AUDITOR,
        dependencies=["task_01"],
    )
    assert not task.is_unblocked
    assert not task.is_terminal
    assert not task.is_failed


def test_task_verified_properties() -> None:
    task = Task(
        mission_id="msn_123",
        name="Audit Secrets",
        description="Check repo for secret leaks",
        agent_role=AgentRole.AUDITOR,
        status=TaskStatus.VERIFIED,
    )
    assert task.is_terminal
    assert not task.is_failed


def test_task_failed_properties() -> None:
    task = Task(
        mission_id="msn_123",
        name="Audit Secrets",
        description="Check repo for secret leaks",
        agent_role=AgentRole.AUDITOR,
        status=TaskStatus.FAILED,
    )
    assert not task.is_terminal
    assert task.is_failed


def test_mission_root_entity() -> None:
    goal = Goal(
        goal_statement="Fix auth middleware vulnerability",
        primary_objective="Patch JWT validation vulnerability and verify with unit tests",
        deliverables=["auth_patch.diff", "test_report.json"],
    )
    mission = Mission(
        title="Security Hotfix",
        goal=goal,
    )
    assert mission.mission_id.startswith("msn_")
    assert mission.state.status == MissionStatus.DRAFT
    assert not mission.is_terminal
    assert not mission.is_active


def test_mission_active_state() -> None:
    goal = Goal(
        goal_statement="Fix auth middleware vulnerability",
        primary_objective="Patch JWT validation vulnerability and verify with unit tests",
    )
    mission = Mission(
        title="Security Hotfix",
        goal=goal,
        state=MissionState(status=MissionStatus.EXECUTING),
    )
    assert mission.is_active
    assert not mission.is_terminal


def test_mission_completed_state() -> None:
    goal = Goal(
        goal_statement="Fix auth middleware vulnerability",
        primary_objective="Patch JWT validation vulnerability and verify with unit tests",
    )
    mission = Mission(
        title="Security Hotfix",
        goal=goal,
        state=MissionState(status=MissionStatus.COMPLETED),
    )
    assert mission.is_terminal
    assert not mission.is_active

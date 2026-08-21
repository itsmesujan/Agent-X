"""Unit tests for Agent-X Goal Engine."""

import pytest

from agentx.goal_engine import (
    GoalEngine,
    GoalInputOverrides,
    MalformedMissionError,
    ParsedGoalOutput,
    RequiredCapability,
    RiskLevel,
)
from agentx.kernel.models import SuccessCriteria
from agentx.llm import LLMAuthenticationError, LLMResourceExhaustedError, MockLLMProvider
from agentx_common.schemas import MissionBudget, MissionStatus, VerificationLevel


@pytest.fixture
def mock_parsed_goal() -> ParsedGoalOutput:
    return ParsedGoalOutput(
        title="Audit Cloud Run IAM Roles",
        goal_statement="Audit all Cloud Run service accounts in GCP project and flag overprivileged roles.",
        primary_objective="Identify IAM roles exceeding least privilege and produce remediation PR.",
        deliverables=["iam_audit_report.json", "remediation_iam.tf"],
        constraints={"environment": "production", "read_only": True},
        budget=MissionBudget(
            max_usd_limit=4.00, max_total_tokens=500_000, max_execution_time_seconds=1800
        ),
        deadline_seconds=1800,
        success_criteria=[
            SuccessCriteria(
                description="IAM audit report generated in valid JSON format",
                verification_level=VerificationLevel.LEVEL_3_ARTIFACT,
            ),
            SuccessCriteria(
                description="Zero critical permission violations unaddressed",
                verification_level=VerificationLevel.LEVEL_4_SEMANTIC,
            ),
        ],
        risk_level=RiskLevel.HIGH,
        risk_summary="Modifying or auditing security IAM policies on production workloads.",
        required_capabilities=[
            RequiredCapability.SECURITY_AUDIT,
            RequiredCapability.TERRAFORM_PROVISIONING,
            RequiredCapability.CODE_ANALYSIS,
        ],
    )


@pytest.fixture
def goal_engine(mock_parsed_goal: ParsedGoalOutput) -> GoalEngine:
    mock_llm = MockLLMProvider(default_structured_response=mock_parsed_goal)
    return GoalEngine(llm_provider=mock_llm)


def test_goal_deconstruction_success(
    goal_engine: GoalEngine, mock_parsed_goal: ParsedGoalOutput
) -> None:
    raw_prompt = "Audit all Cloud Run IAM roles and ensure least privilege compliance."
    result = goal_engine.deconstruct_goal(raw_prompt)

    assert result.title == "Audit Cloud Run IAM Roles"
    assert result.goal_statement == mock_parsed_goal.goal_statement
    assert result.primary_objective == mock_parsed_goal.primary_objective
    assert len(result.deliverables) == 2
    assert "iam_audit_report.json" in result.deliverables
    assert result.constraints["read_only"] is True
    assert result.budget.max_usd_limit == 4.00
    assert result.deadline_seconds == 1800
    assert len(result.success_criteria) == 2
    assert result.risk_level == RiskLevel.HIGH
    assert RequiredCapability.SECURITY_AUDIT in result.required_capabilities


def test_goal_deconstruction_with_user_overrides(
    goal_engine: GoalEngine, mock_parsed_goal: ParsedGoalOutput
) -> None:
    raw_prompt = "Audit all Cloud Run IAM roles and ensure least privilege compliance."
    overrides = GoalInputOverrides(
        max_usd_budget=8.50,
        max_runtime_minutes=45,
        initial_constraints={"vpc_sc_enabled": True},
        required_deliverables=["compliance_summary.md"],
    )

    result = goal_engine.deconstruct_goal(raw_prompt, overrides=overrides)

    assert result.budget.max_usd_limit == 8.50
    assert result.deadline_seconds == 2700  # 45 * 60
    assert result.budget.max_execution_time_seconds == 2700
    assert result.constraints["vpc_sc_enabled"] is True
    assert "compliance_summary.md" in result.deliverables


def test_goal_deconstruction_empty_prompt_error(goal_engine: GoalEngine) -> None:
    with pytest.raises(MalformedMissionError, match="cannot be empty"):
        goal_engine.deconstruct_goal("   ")


def test_goal_deconstruction_short_prompt_error(goal_engine: GoalEngine) -> None:
    with pytest.raises(MalformedMissionError, match="too short"):
        goal_engine.deconstruct_goal("do task")


def test_goal_engine_llm_rate_limit_propagation() -> None:
    mock_llm = MockLLMProvider()
    mock_llm.set_exception(LLMResourceExhaustedError("Quota exceeded"))
    engine = GoalEngine(llm_provider=mock_llm)

    with pytest.raises(LLMResourceExhaustedError):
        engine.deconstruct_goal("Deploy new backend microservice to Google Cloud Run.")


def test_goal_engine_llm_auth_error_propagation() -> None:
    mock_llm = MockLLMProvider()
    mock_llm.set_exception(LLMAuthenticationError("Invalid API Key"))
    engine = GoalEngine(llm_provider=mock_llm)

    with pytest.raises(LLMAuthenticationError):
        engine.deconstruct_goal("Deploy new backend microservice to Google Cloud Run.")


def test_create_kernel_mission_from_parsed_goal(
    goal_engine: GoalEngine, mock_parsed_goal: ParsedGoalOutput
) -> None:
    mission = goal_engine.create_mission_from_goal(mock_parsed_goal, mission_id="msn_custom_001")

    assert mission.mission_id == "msn_custom_001"
    assert mission.title == "Audit Cloud Run IAM Roles"
    assert mission.status == MissionStatus.DRAFT
    assert mission.goal.primary_objective == mock_parsed_goal.primary_objective
    assert len(mission.goal.deliverables) == 2
    assert len(mission.goal.success_criteria) == 2
    assert mission.metadata["risk_level"] == "HIGH"
    assert "SECURITY_AUDIT" in mission.metadata["required_capabilities"]
    assert mission.metadata["deadline_seconds"] == 1800

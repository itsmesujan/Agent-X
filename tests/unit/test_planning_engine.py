"""Unit tests for Agent-X Strategy and Planning Engine."""

import pytest

from agentx.goal_engine.schemas import RiskLevel
from agentx.kernel.models import Goal, SuccessCriteria
from agentx.llm.mock import MockLLMProvider
from agentx.planning import (
    CandidateStrategiesLLMResponse,
    InvalidStrategyError,
    PlanningContext,
    PlanningEngine,
    StrategyDraftDTO,
    StrategySelectionCriteria,
    StrategyType,
    TaskDraftDTO,
)
from agentx.unknowns.schemas import EpistemicUnknown
from agentx.world_model.models import Constraint, EntityType, Risk, WorldModelEntity
from agentx_common.schemas import AgentRole, MissionBudget, VerificationLevel


def create_sample_planning_context() -> PlanningContext:
    return PlanningContext(
        mission_id="msn_plan_01",
        goal=Goal(
            goal_statement="Remediate Cloud Run IAM permissions and deploy API service",
            primary_objective="Ensure zero public access to sensitive database and deploy Cloud Run API",
            deliverables=["cloud_run_service_url", "security_compliance_report.json"],
        ),
        success_criteria=[
            SuccessCriteria(
                description="Cloud Run endpoint responds 200 to authenticated requests",
                verification_level=VerificationLevel.LEVEL_2_EXECUTION,
            )
        ],
        entities=[
            WorldModelEntity(
                entity_id="cloud_run:api",
                mission_id="msn_plan_01",
                entity_type=EntityType.CLOUD_SERVICE,
                name="agentx-api",
            )
        ],
        unknowns=[
            EpistemicUnknown(
                mission_id="msn_plan_01",
                question="Does agentx-sa have roles/run.admin?",
                impact_description="Blocks deployment",
            )
        ],
        constraints=[
            Constraint(
                mission_id="msn_plan_01",
                name="No plain text secrets",
                rule_statement="Must use Secret Manager",
            )
        ],
        risks=[
            Risk(
                mission_id="msn_plan_01",
                title="Service Account Overprivilege",
                description="Avoid granting Owner role",
                severity=RiskLevel.HIGH,
            )
        ],
        budget=MissionBudget(max_usd_limit=5.00, max_total_tokens=500_000),
        deadline_seconds=1800,
    )


def create_mock_strategies_response() -> CandidateStrategiesLLMResponse:
    # 1. Fast Direct Strategy
    strat_fast = StrategyDraftDTO(
        strategy_id="strat_fast",
        strategy_type=StrategyType.FAST_DIRECT,
        name="Fast Parallel Deployment",
        description="Direct deployment with minimal upfront exploration",
        tasks=[
            TaskDraftDTO(
                task_id="t1_fast",
                name="Direct Deploy Cloud Run",
                description="Deploy service immediately via gcloud",
                agent_role=AgentRole.DEVOPS,
                dependencies=[],
            ),
            TaskDraftDTO(
                task_id="t2_fast",
                name="Smoke Test",
                description="Curl health endpoint",
                agent_role=AgentRole.TESTER,
                dependencies=["t1_fast"],
            ),
        ],
        estimated_cost_usd=1.20,
        estimated_tokens=50_000,
        estimated_duration_seconds=300,
        risk=RiskLevel.HIGH,
        risk_score=0.75,
        expected_success_probability=0.65,
        required_capabilities=[AgentRole.DEVOPS, AgentRole.TESTER],
        tradeoffs=["Fastest completion", "Higher risk of IAM deployment failure"],
    )

    # 2. Balanced Standard Strategy
    strat_balanced = StrategyDraftDTO(
        strategy_id="strat_balanced",
        strategy_type=StrategyType.BALANCED,
        name="Staged Verification & Deployment",
        description="Explores unknowns first, applies Terraform, runs tests",
        tasks=[
            TaskDraftDTO(
                task_id="t1_bal",
                name="Inspect IAM Permissions",
                description="Check service account roles",
                agent_role=AgentRole.DEVOPS,
                dependencies=[],
            ),
            TaskDraftDTO(
                task_id="t2_bal",
                name="Deploy via Terraform",
                description="Apply Terraform configuration",
                agent_role=AgentRole.DEVOPS,
                dependencies=["t1_bal"],
            ),
            TaskDraftDTO(
                task_id="t3_bal",
                name="Run Integration Test Suite",
                description="Execute automated tests",
                agent_role=AgentRole.TESTER,
                dependencies=["t2_bal"],
            ),
            TaskDraftDTO(
                task_id="t4_bal",
                name="Audit Security Posture",
                description="Verify compliance report",
                agent_role=AgentRole.AUDITOR,
                dependencies=["t3_bal"],
            ),
        ],
        estimated_cost_usd=2.50,
        estimated_tokens=150_000,
        estimated_duration_seconds=800,
        risk=RiskLevel.LOW,
        risk_score=0.20,
        expected_success_probability=0.92,
        required_capabilities=[AgentRole.DEVOPS, AgentRole.TESTER, AgentRole.AUDITOR],
        tradeoffs=["High success rate", "Balanced duration and cost"],
    )

    # 3. Conservative Hardened Strategy
    strat_hardened = StrategyDraftDTO(
        strategy_id="strat_hardened",
        strategy_type=StrategyType.CONSERVATIVE_HARDENED,
        name="Full Defensive Verification",
        description="Exhaustive pre-flight audits and multi-layer verification",
        tasks=[
            TaskDraftDTO(
                task_id="t1_hard",
                name="Deep IAM Audit",
                description="Audit all policy bindings",
                agent_role=AgentRole.AUDITOR,
                dependencies=[],
            ),
            TaskDraftDTO(
                task_id="t2_hard",
                name="Sandbox Dry Run",
                description="Terraform plan and mock deploy",
                agent_role=AgentRole.DEVOPS,
                dependencies=["t1_hard"],
            ),
            TaskDraftDTO(
                task_id="t3_hard",
                name="Production Deploy",
                description="Execute real deployment",
                agent_role=AgentRole.DEVOPS,
                dependencies=["t2_hard"],
            ),
            TaskDraftDTO(
                task_id="t4_hard",
                name="Full Matrix QA",
                description="Run security & performance test suites",
                agent_role=AgentRole.TESTER,
                dependencies=["t3_hard"],
            ),
        ],
        estimated_cost_usd=4.50,
        estimated_tokens=350_000,
        estimated_duration_seconds=1600,
        risk=RiskLevel.LOW,
        risk_score=0.08,
        expected_success_probability=0.98,
        required_capabilities=[AgentRole.AUDITOR, AgentRole.DEVOPS, AgentRole.TESTER],
        tradeoffs=["Near-certain reliability", "Higher token spend and longer execution"],
    )

    return CandidateStrategiesLLMResponse(strategies=[strat_fast, strat_balanced, strat_hardened])


def test_candidate_strategy_generation() -> None:
    mock_llm = MockLLMProvider()
    mock_llm.register_structured_response(
        CandidateStrategiesLLMResponse, create_mock_strategies_response()
    )

    engine = PlanningEngine(llm_provider=mock_llm)
    context = create_sample_planning_context()

    candidates = engine.generate_candidate_strategies(context)

    assert len(candidates) == 3
    assert candidates[0].strategy_type == StrategyType.FAST_DIRECT
    assert candidates[1].strategy_type == StrategyType.BALANCED
    assert candidates[2].strategy_type == StrategyType.CONSERVATIVE_HARDENED

    # Verify task graph instantiation on Balanced strategy
    balanced = candidates[1]
    assert len(balanced.tasks) == 4
    assert balanced.tasks[0].task_id == "t1_bal"
    assert balanced.tasks[1].dependencies == ["t1_bal"]
    assert balanced.tasks[1].idempotency_key != ""


def test_strategy_selection_balanced_default() -> None:
    """Under standard weights, the Balanced strategy should be selected."""
    mock_llm = MockLLMProvider()
    mock_llm.register_structured_response(
        CandidateStrategiesLLMResponse, create_mock_strategies_response()
    )

    engine = PlanningEngine(llm_provider=mock_llm)
    context = create_sample_planning_context()

    result = engine.plan_and_select_strategy(context)

    assert result.selected_strategy.strategy_type == StrategyType.BALANCED
    assert "Selected Strategy: 'Staged Verification & Deployment'" in result.selection_rationale
    assert len(result.candidates_ranked) == 3
    assert result.candidates_ranked[0].strategy.strategy_type == StrategyType.BALANCED


def test_strategy_selection_under_tight_budget() -> None:
    """When budget is constrained to $2.00, only the Fast strategy fits within budget."""
    mock_llm = MockLLMProvider()
    mock_llm.register_structured_response(
        CandidateStrategiesLLMResponse, create_mock_strategies_response()
    )

    engine = PlanningEngine(llm_provider=mock_llm)
    context = create_sample_planning_context()
    context.budget.max_usd_limit = 2.00

    criteria = StrategySelectionCriteria(max_usd_budget=2.00)
    result = engine.plan_and_select_strategy(context, criteria=criteria)

    assert result.selected_strategy.strategy_type == StrategyType.FAST_DIRECT
    assert result.selected_strategy.estimated_cost_usd <= 2.00


def test_strategy_selection_under_extreme_reliability_preference() -> None:
    """When success probability is heavily prioritized (weight=0.80), Conservative strategy wins."""
    mock_llm = MockLLMProvider()
    mock_llm.register_structured_response(
        CandidateStrategiesLLMResponse, create_mock_strategies_response()
    )

    engine = PlanningEngine(llm_provider=mock_llm)
    context = create_sample_planning_context()

    criteria = StrategySelectionCriteria(
        weight_success_probability=0.80,
        weight_risk_penalty=0.15,
        weight_cost_efficiency=0.02,
        weight_speed_efficiency=0.03,
    )
    result = engine.plan_and_select_strategy(context, criteria=criteria)

    assert result.selected_strategy.strategy_type == StrategyType.CONSERVATIVE_HARDENED


def test_cyclic_strategy_dag_rejection() -> None:
    """Test that a candidate strategy with a cyclic dependency is rejected with InvalidStrategyError."""
    cyclic_strat = StrategyDraftDTO(
        strategy_id="strat_cyclic",
        strategy_type=StrategyType.FAST_DIRECT,
        name="Cyclic Strategy",
        description="Contains a cycle",
        tasks=[
            TaskDraftDTO(
                task_id="t1",
                name="Task 1",
                description="Dep on 2",
                agent_role=AgentRole.CODER,
                dependencies=["t2"],
            ),
            TaskDraftDTO(
                task_id="t2",
                name="Task 2",
                description="Dep on 1",
                agent_role=AgentRole.CODER,
                dependencies=["t1"],
            ),
        ],
        estimated_cost_usd=1.0,
        estimated_tokens=10000,
        estimated_duration_seconds=100,
        risk=RiskLevel.HIGH,
        risk_score=0.8,
        expected_success_probability=0.5,
        required_capabilities=[AgentRole.CODER],
    )

    mock_llm = MockLLMProvider()
    mock_llm.register_structured_response(
        CandidateStrategiesLLMResponse,
        CandidateStrategiesLLMResponse(strategies=[cyclic_strat]),
    )

    engine = PlanningEngine(llm_provider=mock_llm)
    context = create_sample_planning_context()

    with pytest.raises(InvalidStrategyError, match="contains cyclic dependencies"):
        engine.generate_candidate_strategies(context)


def test_unknown_dependency_rejection() -> None:
    """Test that a strategy with unknown prerequisite task ID is rejected."""
    bad_dep_strat = StrategyDraftDTO(
        strategy_id="strat_bad",
        strategy_type=StrategyType.BALANCED,
        name="Bad Dep Strategy",
        description="Depends on missing task",
        tasks=[
            TaskDraftDTO(
                task_id="t1",
                name="Task 1",
                description="Dep on nonexistent",
                agent_role=AgentRole.CODER,
                dependencies=["t_nonexistent"],
            )
        ],
        estimated_cost_usd=1.0,
        estimated_tokens=10000,
        estimated_duration_seconds=100,
        risk=RiskLevel.MEDIUM,
        risk_score=0.5,
        expected_success_probability=0.7,
        required_capabilities=[AgentRole.CODER],
    )

    mock_llm = MockLLMProvider()
    mock_llm.register_structured_response(
        CandidateStrategiesLLMResponse,
        CandidateStrategiesLLMResponse(strategies=[bad_dep_strat]),
    )

    engine = PlanningEngine(llm_provider=mock_llm)
    context = create_sample_planning_context()

    with pytest.raises(InvalidStrategyError, match="unknown prerequisite dependency"):
        engine.generate_candidate_strategies(context)

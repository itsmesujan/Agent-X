"""Unit tests for Agent-X Agent Runtime, Capability Registry, Metrics, and Subagents."""

import asyncio
from typing import Any

import pytest

from agentx.runtime import (
    AgentInvocationContext,
    AgentNotFoundError,
    AgentRegistry,
    AgentRuntime,
    AgentStatus,
    AgentType,
    AnalystAgent,
    ArtifactAgent,
    BaseAgent,
    Capability,
    CapabilityRegistry,
    CriticAgent,
    PlannerAgent,
    RecoveryAgent,
    ResearcherAgent,
    VerifierAgent,
)


def make_context(
    agent_type: AgentType,
    task_id: str = "task_run_01",
    mission_id: str = "msn_run_01",
    objective: str = "Test objective",
    inputs: dict[str, Any] | None = None,
    timeout_seconds: float = 5.0,
) -> AgentInvocationContext:
    return AgentInvocationContext(
        task_id=task_id,
        mission_id=mission_id,
        agent_type=agent_type,
        objective=objective,
        inputs=inputs or {},
        timeout_seconds=timeout_seconds,
    )


def test_capability_registry_operations() -> None:
    """Test CapabilityRegistry registration, binding, and discovery."""
    reg = CapabilityRegistry()

    # Verify default capabilities exist
    assert reg.get_capability("planning") is not None
    assert reg.get_capability("verification") is not None

    # Register custom capability
    custom_cap = Capability(
        name="custom_nlp",
        description="Custom NLP parsing",
        required_tools=["spacy"],
    )
    reg.register_capability(custom_cap)
    assert reg.get_capability("custom_nlp") == custom_cap

    # Bind capability to agent
    reg.bind_capability_to_agent("CustomAgent", "custom_nlp")
    agents = reg.find_agents_with_capability("custom_nlp")
    assert "CustomAgent" in agents

    agent_caps = reg.get_capabilities_for_agent("CustomAgent")
    assert len(agent_caps) == 1
    assert agent_caps[0].name == "custom_nlp"


def test_agent_registry_operations() -> None:
    """Test AgentRegistry registration, retrieval, and removal."""
    reg = AgentRegistry()
    planner = PlannerAgent()

    reg.register_agent(planner)
    assert reg.has_agent(AgentType.PLANNER) is True
    assert reg.has_agent("PlannerAgent") is True

    retrieved = reg.get_agent(AgentType.PLANNER)
    assert retrieved == planner

    agents = reg.list_agents()
    assert len(agents) == 1

    # Unregister
    removed = reg.unregister_agent(AgentType.PLANNER)
    assert removed == planner
    assert reg.has_agent(AgentType.PLANNER) is False

    with pytest.raises(AgentNotFoundError):
        reg.get_agent(AgentType.PLANNER)


@pytest.mark.asyncio
async def test_planner_agent_execution() -> None:
    """Test PlannerAgent deconstruction and plan generation."""
    agent = PlannerAgent()
    context = make_context(
        agent_type=AgentType.PLANNER,
        objective="Deploy secure multi-region Firestore backend",
    )
    result = await agent.execute(context)

    assert result.status == AgentStatus.SUCCESS
    assert result.output_data["total_tasks"] == 4
    assert len(result.output_data["tasks"]) == 4
    assert "plan_hash" in result.output_data
    assert result.confidence_score > 0.9


@pytest.mark.asyncio
async def test_researcher_agent_execution() -> None:
    """Test ResearcherAgent gathering structured findings."""
    agent = ResearcherAgent()
    context = make_context(
        agent_type=AgentType.RESEARCHER,
        objective="Find best practices for Cloud Run v2 scaling",
        inputs={"raw_data": ["Concurrency limit 80", "Min instances 1"]},
    )
    result = await agent.execute(context)

    assert result.status == AgentStatus.SUCCESS
    assert result.output_data["findings_count"] == 2
    assert len(result.output_data["findings"]) == 2
    assert result.output_data["findings"][0]["evidence_hash"] is not None


@pytest.mark.asyncio
async def test_analyst_agent_execution() -> None:
    """Test AnalystAgent statistical computations and risk scoring."""
    agent = AnalystAgent()
    context = make_context(
        agent_type=AgentType.ANALYST,
        objective="Compute latency statistics",
        inputs={
            "data_points": [10.0, 20.0, 30.0, 40.0, 50.0],
            "risk_factors": ["High memory usage", "Transient socket drops"],
        },
    )
    result = await agent.execute(context)

    assert result.status == AgentStatus.SUCCESS
    stats = result.output_data["statistical_summary"]
    assert stats["count"] == 5
    assert stats["mean"] == 30.0
    assert stats["min"] == 10.0
    assert stats["max"] == 50.0
    assert result.output_data["overall_risk_score"] > 0.3


@pytest.mark.asyncio
async def test_verifier_agent_execution() -> None:
    """Test VerifierAgent Level 1-4 Verification Protocol."""
    agent = VerifierAgent()
    context = make_context(
        agent_type=AgentType.VERIFIER,
        objective="Verify task output schema and values",
        inputs={
            "target_payload": {"status": "SUCCESS", "records_processed": 100},
            "assertions": [{"key": "status", "value": "SUCCESS"}],
        },
    )
    result = await agent.execute(context)

    assert result.status == AgentStatus.SUCCESS
    assert result.output_data["is_verified"] is True
    assert result.output_data["checks"]["level_1_syntactic"] is True
    assert result.output_data["checks"]["level_2_assertions"] is True
    assert result.output_data["artifact_sha256"] is not None
    assert result.confidence_score == 1.0


@pytest.mark.asyncio
async def test_critic_agent_execution() -> None:
    """Test CriticAgent evaluating acceptance criteria."""
    agent = CriticAgent()
    context = make_context(
        agent_type=AgentType.CRITIC,
        objective="Critique generated documentation",
        inputs={
            "deliverable": {
                "title": "Architecture Guide",
                "summary": "Covers Pub/Sub and Cloud Run",
            },
            "acceptance_criteria": ["Architecture", "Pub/Sub"],
        },
    )
    result = await agent.execute(context)

    assert result.status == AgentStatus.SUCCESS
    assert result.output_data["evaluation_result"] == "PASS"
    assert result.output_data["quality_score"] >= 0.8


@pytest.mark.asyncio
async def test_recovery_agent_execution() -> None:
    """Test RecoveryAgent classifying errors and proposing self-healing actions."""
    agent = RecoveryAgent()
    context = make_context(
        agent_type=AgentType.RECOVERY,
        objective="Diagnose failure",
        inputs={
            "error_message": "HTTP 429: Resource exhausted / rate limit exceeded",
            "retry_count": 1,
        },
    )
    result = await agent.execute(context)

    assert result.status == AgentStatus.SUCCESS
    assert result.output_data["error_category"] == "RATE_LIMIT"
    assert result.output_data["recommended_action"] == "BACKOFF_AND_RETRY"
    assert result.output_data["can_auto_recover"] is True


@pytest.mark.asyncio
async def test_artifact_agent_execution() -> None:
    """Test ArtifactAgent compiling markdown deliverable and manifest."""
    agent = ArtifactAgent()
    context = make_context(
        agent_type=AgentType.ARTIFACT,
        objective="Compile architecture document",
        inputs={
            "title": "Agent-X Architecture Overview",
            "sections": {
                "Overview": "System architecture document",
                "Security": "Least privilege IAM",
            },
        },
    )
    result = await agent.execute(context)

    assert result.status == AgentStatus.SUCCESS
    assert len(result.artifacts) == 1
    assert result.artifacts[0]["filename"] == "mission_deliverable.md"
    assert result.output_data["primary_artifact_sha256"] is not None


class SlowMockAgent(BaseAgent):
    """Mock agent designed to simulate long execution for timeout tests."""

    def __init__(self) -> None:
        super().__init__(
            agent_type=AgentType.PLANNER,
            name="SlowMockAgent",
        )

    async def _execute_internal(self, context: AgentInvocationContext) -> dict[str, Any]:
        await asyncio.sleep(0.5)
        return {"done": True}


class FailingMockAgent(BaseAgent):
    """Mock agent designed to simulate unhandled exception."""

    def __init__(self) -> None:
        super().__init__(
            agent_type=AgentType.CRITIC,
            name="FailingMockAgent",
        )

    async def _execute_internal(self, context: AgentInvocationContext) -> dict[str, Any]:
        raise ValueError("Simulated unexpected agent failure")


@pytest.mark.asyncio
async def test_runtime_timeout_enforcement() -> None:
    """Test AgentRuntime enforcing strict timeout limits."""
    runtime = AgentRuntime(auto_register_default_agents=False)
    runtime.agent_registry.register_agent(SlowMockAgent())

    context = make_context(
        agent_type=AgentType.PLANNER,
        timeout_seconds=0.05,  # 50ms timeout
    )
    result = await runtime.invoke(AgentType.PLANNER, context, timeout_seconds=0.05)

    assert result.status == AgentStatus.TIMEOUT
    assert "exceeded timeout" in (result.error_details or "")

    metrics = runtime.get_metrics(AgentType.PLANNER)
    assert metrics.timeout_count == 1
    assert metrics.success_count == 0


@pytest.mark.asyncio
async def test_runtime_failure_handling() -> None:
    """Test AgentRuntime capturing unhandled exceptions without crashing."""
    runtime = AgentRuntime(auto_register_default_agents=False)
    runtime.agent_registry.register_agent(FailingMockAgent())

    context = make_context(agent_type=AgentType.CRITIC)
    result = await runtime.invoke(AgentType.CRITIC, context)

    assert result.status == AgentStatus.FAILED
    assert "Simulated unexpected agent failure" in (result.error_details or "")

    metrics = runtime.get_metrics(AgentType.CRITIC)
    assert metrics.failure_count == 1
    assert metrics.success_count == 0


@pytest.mark.asyncio
async def test_runtime_performance_metrics_tracking() -> None:
    """Test aggregate and per-agent metrics tracking across multiple invocations."""
    runtime = AgentRuntime(auto_register_default_agents=True)

    # 1. Invoke Researcher
    res_ctx = make_context(agent_type=AgentType.RESEARCHER)
    res_result = await runtime.invoke(AgentType.RESEARCHER, res_ctx)
    assert res_result.status == AgentStatus.SUCCESS

    # 2. Invoke Verifier
    ver_ctx = make_context(agent_type=AgentType.VERIFIER)
    ver_result = await runtime.invoke(AgentType.VERIFIER, ver_ctx)
    assert ver_result.status == AgentStatus.SUCCESS

    # Check metrics
    res_metrics = runtime.get_metrics(AgentType.RESEARCHER)
    assert res_metrics.total_invocations == 1
    assert res_metrics.success_count == 1
    assert res_metrics.total_tokens_used > 0

    global_metrics = runtime.get_metrics("GLOBAL")
    assert global_metrics.total_invocations == 2
    assert global_metrics.success_count == 2
    assert global_metrics.success_rate == 100.0

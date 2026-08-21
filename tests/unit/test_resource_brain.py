"""Unit tests for Agent-X Resource Brain."""

import pytest

from agentx.kernel.events import EventBus, EventType, ResourceEvent
from agentx.kernel.models import Task
from agentx.resource_brain import (
    ModelTier,
    ResourceBrain,
    ResourceExhaustedError,
    calculate_llm_cost,
)
from agentx_common.schemas import AgentRole, MissionBudget, TaskStatus


def create_sample_task(
    task_id: str = "task_01",
    name: str = "Inspect IAM",
    agent_role: AgentRole = AgentRole.DEVOPS,
) -> Task:
    return Task(
        task_id=task_id,
        mission_id="msn_rb_01",
        name=name,
        description="Task description",
        agent_role=agent_role,
        status=TaskStatus.PENDING,
        timeout_seconds=120,
    )


def test_pricing_math() -> None:
    """Test exact pricing calculations for Flash and Pro models."""
    # 10,000 input, 2,000 output with Flash
    cost_flash = calculate_llm_cost(
        ModelTier.GEMINI_2_5_FLASH, input_tokens=10_000, output_tokens=2_000
    )
    assert cost_flash > 0.0
    assert cost_flash < 0.01

    # 10,000 input, 2,000 output with Pro
    cost_pro = calculate_llm_cost(
        ModelTier.GEMINI_2_5_PRO, input_tokens=10_000, output_tokens=2_000
    )
    assert cost_pro > cost_flash


def test_dynamic_model_routing_flash_vs_pro() -> None:
    """Verify that routine/exploratory tasks route to Flash while deep reasoning routes to Pro."""
    events = EventBus()
    brain = ResourceBrain(mission_id="msn_rb_01", event_bus=events)

    # 1. Exploratory sensory task
    sensory_task = create_sample_task(
        task_id="t_log", name="Extract Error Logs", agent_role=AgentRole.TESTER
    )
    pred_flash = brain.predict_task_resources(
        sensory_task, reasoning_depth=0.2, code_size=0.1, is_exploratory=True
    )
    assert pred_flash.predicted_model == ModelTier.GEMINI_2_5_FLASH
    assert "Gemini 2.5 Flash" in pred_flash.explanation

    # 2. Deep architectural planning task
    arch_task = create_sample_task(
        task_id="t_arch", name="Synthesize Architecture", agent_role=AgentRole.ARCHITECT
    )
    pred_pro = brain.predict_task_resources(
        arch_task, reasoning_depth=0.9, code_size=0.7, requires_deep_reasoning=True
    )
    assert pred_pro.predicted_model == ModelTier.GEMINI_2_5_PRO
    assert "Gemini 2.5 Pro" in pred_pro.explanation


def test_allocation_and_reservation_flow() -> None:
    """Test resource reservation, agent slot acquisition, and event emission."""
    events = EventBus()
    budget = MissionBudget(max_usd_limit=5.00, max_total_tokens=500_000)
    brain = ResourceBrain(mission_id="msn_rb_01", budget=budget, event_bus=events)

    task = create_sample_task(task_id="t_res_01", agent_role=AgentRole.CODER)

    decision = brain.request_allocation(task, reasoning_depth=0.7)

    assert decision.is_granted is True
    assert decision.selected_model == ModelTier.GEMINI_2_5_PRO
    assert decision.reservation_id is not None
    assert "Granted allocation" in decision.explanation

    # Check agent lease acquired
    assert "t_res_01" in brain.agent_pool.active_leases["CODER"]

    # Check event emitted
    recorded_events = events.get_events("msn_rb_01")
    reserved_events = [
        e
        for e in recorded_events
        if isinstance(e, ResourceEvent) and e.event_type == EventType.RESOURCE_RESERVED
    ]
    assert len(reserved_events) == 1
    assert reserved_events[0].amount_usd > 0


def test_consumption_recording_and_budget_warning() -> None:
    """Test consumption tracking and automatic 80% budget warning trigger."""
    events = EventBus()
    budget = MissionBudget(max_usd_limit=1.00, max_total_tokens=100_000)
    brain = ResourceBrain(mission_id="msn_rb_01", budget=budget, event_bus=events)

    task = create_sample_task(task_id="t_cns_01")
    brain.request_allocation(task)

    # Consume $0.85 (85% of $1.00 budget)
    # Pro model: ~160,000 output tokens * $5/M = $0.80
    consumption = brain.record_consumption(
        task_id="t_cns_01",
        input_tokens=10_000,
        output_tokens=170_000,
        actual_duration_seconds=45,
        model=ModelTier.GEMINI_2_5_PRO,
    )

    assert consumption.actual_cost_usd >= 0.80
    assert brain.budget.current_usd_spent >= 0.80

    # Verify Budget Warning Event Emitted
    recorded = events.get_events("msn_rb_01")
    warning_events = [
        e
        for e in recorded
        if isinstance(e, ResourceEvent) and e.event_type == EventType.BUDGET_WARNING
    ]
    assert len(warning_events) == 1
    assert "80% of budget cap" in warning_events[0].details["message"]


def test_budget_exhaustion_refusal() -> None:
    """Test that reaching 100% budget emits BUDGET_EXHAUSTED and refuses new allocations."""
    events = EventBus()
    budget = MissionBudget(max_usd_limit=0.50, max_total_tokens=50_000)
    brain = ResourceBrain(mission_id="msn_rb_01", budget=budget, event_bus=events)

    # 1. Exhaust budget directly
    brain.record_consumption(
        task_id="t_prior",
        input_tokens=50_000,
        output_tokens=100_000,
        model=ModelTier.GEMINI_2_5_PRO,
    )
    assert brain.budget.current_usd_spent >= 0.50

    exhausted_events = [
        e for e in events.get_events("msn_rb_01") if e.event_type == EventType.BUDGET_EXHAUSTED
    ]
    assert len(exhausted_events) >= 1

    # 2. Subsequent allocation request must be refused
    next_task = create_sample_task(task_id="t_next")
    decision = brain.request_allocation(next_task)

    assert decision.is_granted is False
    assert decision.refusal_reason is not None
    assert "Budget Exhausted" in decision.refusal_reason


def test_agent_concurrency_and_tool_locks() -> None:
    """Test concurrency slots and exclusive tool lock management."""
    events = EventBus()
    brain = ResourceBrain(mission_id="msn_rb_01", event_bus=events)

    # Coordinator max slots = 1
    t_coord_1 = create_sample_task(task_id="t_c1", agent_role=AgentRole.COORDINATOR)
    t_coord_2 = create_sample_task(task_id="t_c2", agent_role=AgentRole.COORDINATOR)

    d1 = brain.request_allocation(t_coord_1)
    assert d1.is_granted is True

    d2 = brain.request_allocation(t_coord_2)
    assert d2.is_granted is False
    assert "Agent concurrency ceiling reached" in str(d2.refusal_reason)

    # Release t_coord_1
    brain.release_reservation("t_c1")
    assert len(brain.agent_pool.active_leases["COORDINATOR"]) == 0

    # Exclusive tool locking (e.g. terraform_apply)
    t_tf1 = create_sample_task(task_id="t_tf1", agent_role=AgentRole.DEVOPS)
    t_tf2 = create_sample_task(task_id="t_tf2", agent_role=AgentRole.DEVOPS)

    d_tf1 = brain.request_allocation(t_tf1, required_tools=["terraform_apply"])
    assert d_tf1.is_granted is True
    assert brain.tool_pool.active_tool_locks["terraform_apply"] == "t_tf1"

    d_tf2 = brain.request_allocation(t_tf2, required_tools=["terraform_apply"])
    assert d_tf2.is_granted is False
    assert "Exclusive tool 'terraform_apply' is currently locked" in str(d_tf2.refusal_reason)

    # Release tool lock
    brain.release_reservation("t_tf1")
    assert "terraform_apply" not in brain.tool_pool.active_tool_locks


def test_reallocation_and_human_attention() -> None:
    """Test budget reallocation and human attention rate-limiting."""
    events = EventBus()
    brain = ResourceBrain(mission_id="msn_rb_01", event_bus=events)

    # Reallocation
    brain.reallocate_budget(
        from_task_id="t_cheap",
        to_task_id="t_complex",
        usd_amount=1.50,
        tokens=100_000,
        reason="Transferred savings from completed discovery",
    )

    realloc_events = [
        e
        for e in events.get_events("msn_rb_01")
        if isinstance(e, ResourceEvent) and e.event_type == EventType.RESOURCE_REALLOCATED
    ]
    assert len(realloc_events) == 1
    assert realloc_events[0].amount_usd == 1.50

    # Human attention quota (max 5 interrupts)
    for _ in range(5):
        assert brain.request_human_attention("Review security report") is True

    # 6th interrupt must be rejected
    assert brain.request_human_attention("Exceeded quota request") is False


def test_storage_quota_limit() -> None:
    """Test storage tracking and limit enforcement."""
    brain = ResourceBrain(mission_id="msn_rb_01")

    brain.record_storage(100_000_000)  # 100MB
    assert brain.storage_tracker.current_storage_bytes == 100_000_000

    # Exceed 500MB cap
    with pytest.raises(ResourceExhaustedError, match="Storage quota exceeded"):
        brain.record_storage(450_000_000)


def test_telemetry_snapshot() -> None:
    """Verify aggregated telemetry snapshot."""
    brain = ResourceBrain(
        mission_id="msn_rb_01",
        budget=MissionBudget(max_usd_limit=10.00, max_total_tokens=1_000_000),
        deadline_seconds=3600,
    )

    snapshot = brain.get_telemetry_snapshot()
    assert snapshot["mission_id"] == "msn_rb_01"
    assert snapshot["usd_limit"] == 10.00
    assert snapshot["deadline_seconds"] == 3600
    assert snapshot["human_interrupts_count"] == 0

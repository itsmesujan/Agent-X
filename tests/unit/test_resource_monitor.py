"""Unit and Integration Tests for Agent-X Resource Monitor & Causal Explanations."""

import pytest
from fastapi.testclient import TestClient

from agentx.kernel.events import EventBus, EventType
from agentx.kernel.models import Task
from agentx.main import app
from agentx.resource_brain.brain import ResourceBrain
from agentx.resource_brain.schemas import ResourceDimension
from agentx_common.schemas import AgentRole, MissionBudget, TaskStatus


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def resource_brain(event_bus: EventBus) -> ResourceBrain:
    budget = MissionBudget(
        max_usd_limit=10.0,
        max_total_tokens=1_000_000,
        max_execution_time_seconds=3600,
    )
    return ResourceBrain(
        mission_id="msn_test_monitor_001",
        budget=budget,
        deadline_seconds=3600,
        event_bus=event_bus,
    )


@pytest.fixture
def test_task() -> Task:
    return Task(
        task_id="task_verify_001",
        mission_id="msn_test_monitor_001",
        name="Verify High-Risk Evidence",
        description="Run deep verification against contradictory evidence",
        agent_role=AgentRole.AUDITOR,
        status=TaskStatus.READY,
    )


def test_resource_monitor_initial_dimensions(resource_brain: ResourceBrain) -> None:
    """Verify all 6 dimensions report proper 4-metric tuples on initialization."""
    snapshot = resource_brain.get_monitor_snapshot()
    assert snapshot.mission_id == "msn_test_monitor_001"
    assert len(snapshot.dimensions) == 6

    # 1. Budget
    b = snapshot.dimensions["budget"]
    assert b.allocated == 10.0
    assert b.consumed == 0.0
    assert b.reserved == 0.0
    assert b.remaining == 10.0
    assert b.unit == "USD"

    # 2. Time
    t = snapshot.dimensions["time"]
    assert t.allocated == 3600.0
    assert t.consumed == 0.0
    assert t.remaining == 3600.0
    assert t.unit == "seconds"

    # 3. Compute
    c = snapshot.dimensions["compute"]
    assert c.allocated == 10.0
    assert c.consumed == 0.0
    assert c.remaining == 10.0
    assert c.unit == "slots"

    # 4. API Usage
    api = snapshot.dimensions["api_usage"]
    assert api.allocated == 1_000_000.0
    assert api.consumed == 0.0
    assert api.remaining == 1_000_000.0
    assert api.unit == "tokens"

    # 5. Agent Capacity
    ag = snapshot.dimensions["agent_capacity"]
    assert ag.allocated == 14.0
    assert ag.consumed == 0.0
    assert ag.remaining == 14.0
    assert ag.unit == "slots"

    # 6. Tool Usage
    tl = snapshot.dimensions["tool_usage"]
    assert tl.allocated == 100.0
    assert tl.consumed == 0.0
    assert tl.remaining == 100.0
    assert tl.unit == "runs"


def test_resource_monitor_reservation_and_consumption(
    resource_brain: ResourceBrain, test_task: Task
) -> None:
    """Verify 4-metric tuples update accurately upon task reservation and consumption."""
    # 1. Request Allocation
    decision = resource_brain.request_allocation(test_task, reasoning_depth=0.8)
    assert decision.is_granted is True

    snapshot1 = resource_brain.get_monitor_snapshot()
    b1 = snapshot1.dimensions["budget"]
    assert b1.consumed == 0.0
    assert b1.reserved > 0.0
    assert b1.remaining == pytest.approx(b1.allocated - b1.reserved, abs=1e-4)

    c1 = snapshot1.dimensions["compute"]
    assert c1.consumed == 1.0  # active lease
    assert c1.reserved == 1.0  # active reservation

    # 2. Record Empirical Consumption
    resource_brain.record_consumption(
        task_id=test_task.task_id,
        input_tokens=10_000,
        output_tokens=2_000,
        actual_duration_seconds=45,
    )
    # Release reservation
    resource_brain.release_reservation(test_task.task_id)

    snapshot2 = resource_brain.get_monitor_snapshot()
    b2 = snapshot2.dimensions["budget"]
    assert b2.consumed > 0.0
    assert b2.reserved == 0.0
    assert b2.remaining == pytest.approx(b2.allocated - b2.consumed, abs=1e-4)

    t2 = snapshot2.dimensions["time"]
    assert t2.consumed == 45.0
    assert t2.remaining == 3600.0 - 45.0


def test_causal_allocation_explanation_event(
    resource_brain: ResourceBrain, event_bus: EventBus
) -> None:
    """Verify recording of allocation change generates 'WHY' explanation and publishes event."""
    recorded_events: list = []
    event_bus.subscribe(
        event_type=EventType.RESOURCE_REALLOCATED,
        callback=lambda e: recorded_events.append(e),
    )

    reason_text = "Verification received additional resources because conflicting evidence increased mission risk."
    change = resource_brain.record_allocation_change(
        dimension=ResourceDimension.BUDGET,
        target_name="task_verify_001",
        delta=1.50,
        unit="USD",
        trigger_type="RISK_ELEVATION",
        reason=reason_text,
    )

    assert change.reason == reason_text
    assert change.trigger_type == "RISK_ELEVATION"
    assert change.delta == 1.50
    assert change.target_name == "task_verify_001"

    # Check snapshot history
    snapshot = resource_brain.get_monitor_snapshot()
    assert len(snapshot.reallocation_history) == 1
    assert snapshot.reallocation_history[0].reason == reason_text

    # Check event publication
    assert len(recorded_events) == 1
    assert recorded_events[0].details["reason"] == reason_text


def test_reallocate_budget_records_causal_history(resource_brain: ResourceBrain) -> None:
    """Verify reallocate_budget dynamically logs causal explanation in allocation history."""
    reason = "Reallocated unspent Coder budget to Auditor for deep compliance verification."
    resource_brain.reallocate_budget(
        from_task_id="task_coder_001",
        to_task_id="task_audit_001",
        usd_amount=0.75,
        tokens=50_000,
        reason=reason,
        trigger_type="DYNAMIC_REALLOCATION",
    )

    snapshot = resource_brain.get_monitor_snapshot()
    assert len(snapshot.reallocation_history) == 1
    assert snapshot.reallocation_history[0].reason == reason
    assert snapshot.reallocation_history[0].dimension == ResourceDimension.BUDGET


def test_api_resource_monitor_endpoints() -> None:
    """Test FastAPI GET /resources/monitor and POST /resources/reallocate routes."""
    client = TestClient(app)
    headers = {"Authorization": "Bearer dev-token-operator"}

    # 1. Create a test mission
    res = client.post(
        "/api/v1/missions",
        json={
            "title": "Resource Monitor Integration Test",
            "goal_statement": "Verify API monitor breakdown and causal reallocations.",
            "max_usd_budget": 8.0,
            "max_runtime_minutes": 45,
        },
        headers=headers,
    )
    assert res.status_code == 201
    mission_id = res.json()["mission_id"]

    # 2. Query GET /resources/monitor
    get_res = client.get(f"/api/v1/missions/{mission_id}/resources/monitor", headers=headers)
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["mission_id"] == mission_id
    assert "budget" in data["dimensions"]
    assert "time" in data["dimensions"]
    assert "compute" in data["dimensions"]
    assert "api_usage" in data["dimensions"]
    assert "agent_capacity" in data["dimensions"]
    assert "tool_usage" in data["dimensions"]
    assert data["dimensions"]["budget"]["allocated"] == 8.0

    # 3. Perform POST /resources/reallocate
    why_reason = "Verification received additional resources because conflicting evidence increased mission risk."
    post_res = client.post(
        f"/api/v1/missions/{mission_id}/resources/reallocate",
        json={
            "dimension": "budget",
            "to_target": "task_verification_deep_001",
            "amount": 1.25,
            "unit": "USD",
            "reason": why_reason,
        },
        headers=headers,
    )
    assert post_res.status_code == 200
    realloc_data = post_res.json()
    assert realloc_data["reason"] == why_reason
    assert realloc_data["delta"] == 1.25
    assert realloc_data["dimension"] == "budget"

    # 4. Verify the change is reflected in the monitor history
    get_res_after = client.get(f"/api/v1/missions/{mission_id}/resources/monitor", headers=headers)
    assert get_res_after.status_code == 200
    history = get_res_after.json()["reallocation_history"]
    assert len(history) >= 1
    assert history[-1]["reason"] == why_reason

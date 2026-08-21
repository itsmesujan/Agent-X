"""Unit tests for agentx_common schemas."""

import pytest
from pydantic import ValidationError

from agentx_common.schemas import (
    AgentRole,
    MissionBudget,
    TaskNodeDTO,
    TaskStatus,
)


def test_mission_budget_defaults() -> None:
    budget = MissionBudget()
    assert budget.max_usd_limit == 5.00
    assert budget.max_total_tokens == 1_000_000
    assert budget.max_execution_time_seconds == 3600
    assert budget.current_usd_spent == 0.0


def test_task_node_dto_valid() -> None:
    task = TaskNodeDTO(
        task_id="task-01",
        mission_id="msn-01",
        name="Audit Security",
        description="Audit IAM permissions",
        agent_role=AgentRole.ARCHITECT,
        idempotency_key="idemp_key_01",
    )
    assert task.status == TaskStatus.PENDING
    assert task.retry_count == 0
    assert task.max_retries == 3


def test_invalid_agent_role() -> None:
    with pytest.raises(ValidationError):
        TaskNodeDTO(
            task_id="task-01",
            mission_id="msn-01",
            name="Audit Security",
            description="Audit IAM permissions",
            agent_role="INVALID_ROLE",
            idempotency_key="idemp_key_01",
        )

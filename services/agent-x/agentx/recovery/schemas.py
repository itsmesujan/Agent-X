"""Agent-X Recovery Engine Schemas and Failure Models."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class FailureCategory(StrEnum):
    """The 9 failure categories supported by the Agent-X Error Taxonomy."""

    TRANSIENT = "TRANSIENT"  # Network timeouts, temporary rate limits, socket drops
    TOOL = "TOOL"  # Tool runtime crash, missing tool executable, CLI failure
    DATA = "DATA"  # Schema validation failure, malformed payload, JSON decode error
    RESOURCE = "RESOURCE"  # Token budget exhausted, memory/compute quota, lock timeout
    PERMISSION = "PERMISSION"  # 401/403, missing IAM roles, unauthenticated access
    LOGIC = "LOGIC"  # Test assertion failure, constraint violation, algorithm bug
    MODEL = "MODEL"  # LLM refusal, hallucinated format, prompt injection defense trip
    ENVIRONMENT = "ENVIRONMENT"  # Missing dependency, OS incompatibility, missing env var
    UNKNOWN = "UNKNOWN"  # Unclassified error


class RecoveryStrategyType(StrEnum):
    """The 9 recovery strategies supported by Agent-X."""

    RETRY = "RETRY"  # Immediate retry with same parameters
    BACKOFF = "BACKOFF"  # Exponential backoff with jitter retry
    ALTERNATIVE_TOOL = "ALTERNATIVE_TOOL"  # Route to an alternative compatible tool
    ALTERNATIVE_AGENT = "ALTERNATIVE_AGENT"  # Route task to an alternative agent persona
    TASK_MODIFICATION = "TASK_MODIFICATION"  # Modify task inputs, prompt context, or timeout
    RESOURCE_REALLOCATION = (
        "RESOURCE_REALLOCATION"  # Request quota/budget extension from ResourceBrain
    )
    WORKFLOW_MUTATION = (
        "WORKFLOW_MUTATION"  # Mutate DAG: inject prerequisite setup tasks, split/merge
    )
    REPLANNING = "REPLANNING"  # Trigger PlanningEngine to synthesize a new candidate strategy DAG
    HUMAN_APPROVAL = "HUMAN_APPROVAL"  # Pause mission, emit HITL escalation, await human operator


class FailureDiagnostic(BaseModel):
    """Diagnostic analysis of a task execution failure."""

    model_config = ConfigDict(extra="forbid")

    diagnostic_id: str = Field(default_factory=lambda: f"diag_{uuid4().hex[:10]}")
    task_id: str
    mission_id: str
    category: FailureCategory
    error_message: str
    error_type: str
    stack_trace: str | None = None
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=3, ge=0)
    is_recoverable: bool = Field(default=True)
    diagnosed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RecoveryAction(BaseModel):
    """Concrete recovery action selected to resolve a task failure."""

    model_config = ConfigDict(extra="forbid")

    action_id: str = Field(default_factory=lambda: f"act_{uuid4().hex[:10]}")
    strategy: RecoveryStrategyType
    diagnostic_id: str
    target_task_id: str
    mission_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    reasoning: str
    status: str = Field(default="PROPOSED", description="PROPOSED | APPLIED | FAILED | RESOLVED")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    applied_at: datetime | None = None


class HITLEscalation(BaseModel):
    """Human-in-the-Loop escalation emitted when automated recovery is exhausted or unsafe."""

    model_config = ConfigDict(extra="forbid")

    escalation_id: str = Field(default_factory=lambda: f"hitl_{uuid4().hex[:10]}")
    mission_id: str
    task_id: str
    error_category: FailureCategory
    diagnosis: str
    attempted_strategies: list[str] = Field(default_factory=list)
    suggested_human_actions: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

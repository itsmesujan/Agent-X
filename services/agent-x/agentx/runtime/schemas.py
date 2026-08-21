"""Agent-X Agent Runtime Core Domain Models and Schemas."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentType(StrEnum):
    """Supported specialized agent personas in Agent-X."""

    PLANNER = "PLANNER"
    RESEARCHER = "RESEARCHER"
    ANALYST = "ANALYST"
    VERIFIER = "VERIFIER"
    CRITIC = "CRITIC"
    RECOVERY = "RECOVERY"
    ARTIFACT = "ARTIFACT"


class AgentStatus(StrEnum):
    """Operational status of an agent or agent invocation."""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    DISABLED = "DISABLED"


class Capability(BaseModel):
    """Represents a specific skill or capability provided by an agent."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Unique name of the capability")
    description: str = Field(..., description="Description of what this capability achieves")
    required_tools: list[str] = Field(
        default_factory=list, description="Tools needed to exercise capability"
    )
    version: str = Field(default="1.0.0", description="Capability schema version")


class AgentInvocationContext(BaseModel):
    """Input payload dispatched to an agent for task execution."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(..., description="Unique task identifier")
    mission_id: str = Field(..., description="Parent mission identifier")
    agent_type: AgentType = Field(..., description="Target specialized agent type")
    objective: str = Field(..., description="Actionable task objective")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Resolved input arguments")
    allowed_tools: list[str] = Field(
        default_factory=list, description="Whitelisted tools available for this execution"
    )
    timeout_seconds: float = Field(default=300.0, gt=0, description="Hard timeout in seconds")
    token_budget: int = Field(default=50000, gt=0, description="Max token allocation")
    verification_level: str = Field(
        default="LEVEL_3_ARTIFACT", description="Target verification standard"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary context metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentResult(BaseModel):
    """Execution outcome produced by an agent invocation."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(..., description="Task ID this result corresponds to")
    agent_type: AgentType = Field(..., description="Agent type that performed the work")
    status: AgentStatus = Field(..., description="Execution status")
    output_data: dict[str, Any] = Field(
        default_factory=dict, description="Structured output payload"
    )
    artifacts: list[dict[str, Any]] = Field(
        default_factory=list, description="Generated file artifacts or data blobs"
    )
    confidence_score: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Self-assessed confidence score"
    )
    execution_time_ms: float = Field(default=0.0, ge=0.0, description="Execution latency in ms")
    tokens_used: int = Field(default=0, ge=0, description="Total tokens consumed")
    cost_usd: float = Field(default=0.0, ge=0.0, description="Calculated API cost in USD")
    error_details: str | None = Field(
        default=None, description="Diagnostic error trace if status != SUCCESS"
    )
    completed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentPerformanceMetrics(BaseModel):
    """Performance and reliability metrics for an individual agent type or global runtime."""

    model_config = ConfigDict(extra="forbid")

    agent_type: str = Field(..., description="Agent type or 'GLOBAL'")
    total_invocations: int = Field(default=0, ge=0)
    success_count: int = Field(default=0, ge=0)
    failure_count: int = Field(default=0, ge=0)
    timeout_count: int = Field(default=0, ge=0)
    total_duration_ms: float = Field(default=0.0, ge=0.0)
    avg_duration_ms: float = Field(default=0.0, ge=0.0)
    total_tokens_used: int = Field(default=0, ge=0)
    total_cost_usd: float = Field(default=0.0, ge=0.0)
    success_rate: float = Field(default=100.0, ge=0.0, le=100.0)


class AgentExecutionError(Exception):
    """Raised when an agent execution fails or encounters a critical error."""

    def __init__(
        self,
        agent_type: AgentType | str,
        task_id: str,
        message: str,
        details: str | None = None,
    ) -> None:
        self.agent_type = agent_type
        self.task_id = task_id
        self.details = details
        super().__init__(f"Agent '{agent_type}' failed on task '{task_id}': {message}")


class AgentTimeoutError(AgentExecutionError):
    """Raised when an agent exceeds its allotted execution timeout."""

    def __init__(self, agent_type: AgentType | str, task_id: str, timeout_seconds: float) -> None:
        super().__init__(
            agent_type=agent_type,
            task_id=task_id,
            message=f"Execution timed out after {timeout_seconds:.2f} seconds",
            details="Hard timeout threshold exceeded",
        )

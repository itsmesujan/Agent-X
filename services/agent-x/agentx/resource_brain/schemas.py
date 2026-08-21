"""Agent-X Resource Brain Domain Models and Governance Schemas."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from agentx_common.schemas import AgentRole


class ModelTier(StrEnum):
    """Supported Gemini LLM model tiers for dynamic routing."""

    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_FLASH_THINKING = "gemini-2.5-flash-thinking"
    GEMINI_3_7_FLASH = "gemini-3.7-flash"
    GEMINI_3_1_PRO = "gemini-3.1-pro"


class TaskComplexityEstimate(BaseModel):
    """Multi-variable task complexity assessment for dynamic model routing."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    reasoning_depth: float = Field(default=0.5, ge=0.0, le=1.0)
    code_size: float = Field(default=0.3, ge=0.0, le=1.0)
    tool_count: int = Field(default=1, ge=0)
    is_exploratory: bool = False
    requires_deep_reasoning: bool = False
    complexity_score: float = Field(default=0.5, ge=0.0, le=1.0)


class ResourcePrediction(BaseModel):
    """Predictive estimate of required tokens, duration, and financial cost."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    predicted_model: ModelTier
    predicted_input_tokens: int
    predicted_output_tokens: int
    predicted_total_tokens: int
    predicted_cost_usd: float
    predicted_duration_seconds: int
    complexity_score: float
    explanation: str


class ResourceReservation(BaseModel):
    """Active reservation holding resources prior to task dispatch."""

    model_config = ConfigDict(extra="forbid")

    reservation_id: str = Field(default_factory=lambda: f"res_{uuid4().hex[:10]}")
    mission_id: str
    task_id: str
    model: ModelTier
    reserved_tokens: int
    reserved_cost_usd: float
    reserved_duration_seconds: int
    reserved_agent_role: AgentRole
    reserved_tools: list[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ResourceConsumption(BaseModel):
    """Empirical record of actual resources consumed by a task."""

    model_config = ConfigDict(extra="forbid")

    consumption_id: str = Field(default_factory=lambda: f"cns_{uuid4().hex[:10]}")
    mission_id: str
    task_id: str
    model: ModelTier
    input_tokens: int
    output_tokens: int
    cached_tokens: int = 0
    total_tokens: int
    actual_cost_usd: float
    actual_duration_seconds: int
    storage_bytes: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AllocationDecision(BaseModel):
    """Explainable resource allocation decision granting or refusing execution."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    is_granted: bool
    selected_model: ModelTier | None = None
    allocated_tokens: int = 0
    timeout_seconds: int = 0
    reserved_cost_usd: float = 0.0
    assigned_role: AgentRole | None = None
    reservation_id: str | None = None
    explanation: str
    refusal_reason: str | None = None


class ResourceLedgerEntry(BaseModel):
    """Immutable transaction entry in the mission resource ledger."""

    model_config = ConfigDict(extra="forbid")

    entry_id: str = Field(default_factory=lambda: f"led_{uuid4().hex[:12]}")
    mission_id: str
    task_id: str | None = None
    mutation_type: (
        str  # "RESERVATION" | "CONSUMPTION" | "RELEASE" | "REALLOCATION" | "WARNING" | "EXHAUSTED"
    )
    amount_usd: float = 0.0
    tokens: int = 0
    duration_seconds: int = 0
    storage_bytes: int = 0
    details: dict[str, Any] = Field(default_factory=dict)
    running_usd_spent: float = 0.0
    running_tokens_used: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentAvailabilityPool(BaseModel):
    """Tracks concurrency worker slots per specialized agent role."""

    model_config = ConfigDict(extra="forbid")

    max_slots_per_role: dict[str, int] = Field(
        default_factory=lambda: {
            "COORDINATOR": 1,
            "ARCHITECT": 2,
            "CODER": 4,
            "TESTER": 3,
            "DEVOPS": 2,
            "AUDITOR": 2,
        }
    )
    active_leases: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "COORDINATOR": list[str](),
            "ARCHITECT": list[str](),
            "CODER": list[str](),
            "TESTER": list[str](),
            "DEVOPS": list[str](),
            "AUDITOR": list[str](),
        }
    )


class ToolAvailabilityPool(BaseModel):
    """Tracks tool concurrency locks and rate quotas."""

    model_config = ConfigDict(extra="forbid")

    exclusive_tools: list[str] = Field(
        default_factory=lambda: ["terraform_apply", "database_migration"]
    )
    active_tool_locks: dict[str, str] = Field(default_factory=dict)  # tool_name -> task_id
    rpm_limits: dict[str, int] = Field(
        default_factory=lambda: {"gemini_api": 100, "gcloud_cli": 60}
    )
    current_minute_requests: dict[str, int] = Field(default_factory=dict)


class HumanAttentionTracker(BaseModel):
    """Tracks HITL escalation interrupts to prevent operator fatigue."""

    model_config = ConfigDict(extra="forbid")

    max_interrupts_allowed: int = 5
    current_interrupts: int = 0
    pending_approvals: int = 0
    last_interaction_at: datetime | None = None


class StorageQuotaTracker(BaseModel):
    """Tracks mission artifact disk/cloud storage consumption."""

    model_config = ConfigDict(extra="forbid")

    max_storage_bytes: int = 500_000_000  # 500MB
    current_storage_bytes: int = 0


class ResourceDimension(StrEnum):
    """Core dimensions monitored by the Resource Brain."""

    BUDGET = "budget"
    TIME = "time"
    COMPUTE = "compute"
    API_USAGE = "api_usage"
    AGENT_CAPACITY = "agent_capacity"
    TOOL_USAGE = "tool_usage"


class ResourceMetricTuple(BaseModel):
    """Four-metric resource allocation breakdown."""

    model_config = ConfigDict(extra="forbid")

    allocated: float
    consumed: float
    remaining: float
    reserved: float
    unit: str


class AllocationChangeEvent(BaseModel):
    """Chronological record explaining WHY an allocation change occurred."""

    model_config = ConfigDict(extra="forbid")

    change_id: str = Field(default_factory=lambda: f"alc_{uuid4().hex[:12]}")
    mission_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    dimension: ResourceDimension
    target_name: str
    previous_allocated: float
    new_allocated: float
    delta: float
    unit: str
    trigger_type: str  # e.g. "RISK_ELEVATION", "CONFLICTING_EVIDENCE", "RETRY_BACKOFF", "MODEL_ROUTING", "PARALLEL_SPLIT"
    reason: str


class ResourceMonitorSnapshot(BaseModel):
    """Comprehensive multi-dimensional Resource Monitor snapshot."""

    model_config = ConfigDict(extra="forbid")

    mission_id: str
    dimensions: dict[str, ResourceMetricTuple]
    agent_breakdown: dict[str, ResourceMetricTuple]
    tool_breakdown: dict[str, ResourceMetricTuple]
    reallocation_history: list[AllocationChangeEvent]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

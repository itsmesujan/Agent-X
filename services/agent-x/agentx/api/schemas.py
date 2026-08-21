"""Agent-X FastAPI Request and Response DTO Schemas."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agentx_common.schemas import AgentRole, MissionBudget, MissionStatus, TaskStatus

# --- 1. MISSION SCHEMAS ---


class CreateMissionRequest(BaseModel):
    """Payload to create and formulate a new mission."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=3, max_length=200, description="Mission display title")
    goal_statement: str = Field(..., min_length=5, description="High-level user goal statement")
    max_usd_budget: float = Field(default=5.00, gt=0.0, description="Max dollar spending limit")
    max_runtime_minutes: int = Field(default=60, gt=0, description="Max allowed execution duration")
    deliverables: list[str] = Field(
        default_factory=list, description="Expected deliverable filenames"
    )
    constraints: dict[str, Any] = Field(default_factory=dict, description="Operational constraints")


class CreateMissionResponse(BaseModel):
    """Response returned upon mission initialization."""

    model_config = ConfigDict(extra="forbid")

    mission_id: str
    status: MissionStatus
    title: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MissionSummaryDTO(BaseModel):
    """Compact summary of a mission for dashboard listings."""

    model_config = ConfigDict(extra="forbid")

    mission_id: str
    title: str
    status: MissionStatus
    current_usd_spent: float
    max_usd_limit: float
    task_count: int
    created_at: datetime


class MissionDetailDTO(BaseModel):
    """Comprehensive details of a mission including budget and progress metrics."""

    model_config = ConfigDict(extra="forbid")

    mission_id: str
    title: str
    goal_statement: str
    primary_objective: str
    status: MissionStatus
    budget: MissionBudget
    deliverables: list[str]
    constraints: dict[str, Any]
    summary: dict[str, int] = Field(
        description="Task status breakdown (total, verified, running, failed)"
    )
    created_at: datetime
    updated_at: datetime


# --- 2. TASK & GRAPH SCHEMAS ---


class TaskDTO(BaseModel):
    """Detailed representation of a task node."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    mission_id: str
    name: str
    description: str
    agent_role: AgentRole
    status: TaskStatus
    dependencies: list[str]
    dependent_children: list[str]
    retry_count: int
    allocated_tokens: int
    evidence_uri: str | None = None


class WorkflowGraphNodeDTO(BaseModel):
    """Node in the visual DAG representation."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    agent_role: AgentRole
    status: TaskStatus
    retry_count: int


class WorkflowGraphEdgeDTO(BaseModel):
    """Directed edge in the visual DAG representation."""

    model_config = ConfigDict(extra="forbid")

    source: str
    target: str


class WorkflowGraphDTO(BaseModel):
    """Complete graph topology for mission control visualization."""

    model_config = ConfigDict(extra="forbid")

    mission_id: str
    nodes: list[WorkflowGraphNodeDTO]
    edges: list[WorkflowGraphEdgeDTO]


# --- 3. EVENT SCHEMAS ---


class EventDTO(BaseModel):
    """Serialized kernel event for audit trails and telemetry."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    mission_id: str
    event_type: str
    timestamp: datetime
    payload: dict[str, Any]


# --- 4. RESOURCE & EVIDENCE SCHEMAS ---


class ResourceSummaryDTO(BaseModel):
    """Quantitative snapshot of resource budget, tokens, and active locks."""

    model_config = ConfigDict(extra="forbid")

    mission_id: str
    max_usd_limit: float
    current_usd_spent: float
    max_total_tokens: int
    current_tokens_used: int
    current_execution_time_seconds: int
    active_agent_leases: dict[str, list[str]]
    active_tool_locks: dict[str, str]


class ResourceMetricTupleDTO(BaseModel):
    """Four-metric resource allocation breakdown."""

    model_config = ConfigDict(extra="forbid")

    allocated: float
    consumed: float
    remaining: float
    reserved: float
    unit: str


class AllocationChangeEventDTO(BaseModel):
    """Chronological record explaining WHY an allocation change occurred."""

    model_config = ConfigDict(extra="forbid")

    change_id: str
    mission_id: str
    timestamp: datetime
    dimension: str
    target_name: str
    previous_allocated: float
    new_allocated: float
    delta: float
    unit: str
    trigger_type: str
    reason: str


class ResourceMonitorResponseDTO(BaseModel):
    """Comprehensive multi-dimensional Resource Monitor response."""

    model_config = ConfigDict(extra="forbid")

    mission_id: str
    dimensions: dict[str, ResourceMetricTupleDTO]
    agent_breakdown: dict[str, ResourceMetricTupleDTO]
    tool_breakdown: dict[str, ResourceMetricTupleDTO]
    reallocation_history: list[AllocationChangeEventDTO]
    timestamp: datetime


class ManualReallocationRequest(BaseModel):
    """Request payload to manually reallocate mission resources with mandatory justification."""

    model_config = ConfigDict(extra="forbid")

    dimension: str = (
        "budget"  # "budget" | "time" | "compute" | "api_usage" | "agent_capacity" | "tool_usage"
    )
    from_target: str = "general_pool"
    to_target: str
    amount: float = Field(gt=0.0)
    unit: str = "USD"
    reason: str = Field(min_length=5)


class EvidenceItemDTO(BaseModel):
    """Immutable evidence artifact with cryptographic hash and storage attribution."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    source_uri: str
    content_ref: str
    raw_data_hash: str
    byte_size: int = 0
    collected_by_agent: str | None = None
    task_id: str | None = None
    timestamp: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClaimConflictDTO(BaseModel):
    """Contradiction or disagreement detected between two claims."""

    model_config = ConfigDict(extra="forbid")

    conflict_id: str
    claim_a_id: str
    claim_b_id: str
    subject: str
    predicate: str
    value_a: Any
    value_b: Any
    reason: str
    severity: str = "MODERATE"
    is_resolved: bool = False
    resolution_notes: str | None = None
    resolved_at: datetime | None = None


class EvidenceClaimDTO(BaseModel):
    """Rich empirical claim model with supporting evidence items and causal decision reasoning."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str
    mission_id: str
    statement: str
    subject: str
    predicate: str
    value: Any
    source_ref: str
    source_reliability: str
    confidence: float
    status: str
    content_ref: str
    evidence_items: list[EvidenceItemDTO] = Field(default_factory=list)
    conflict_ids: list[str] = Field(default_factory=list)
    conflicts: list[ClaimConflictDTO] = Field(default_factory=list)
    invalidation_reason: str | None = None
    superseded_by_claim_id: str | None = None
    final_decision_reason: str
    created_at: datetime
    updated_at: datetime
    verified_at: datetime | None = None


class EvidenceSummaryDTO(BaseModel):
    """Summary of empirical claims, evidence proofs, conflicts, and traces."""

    model_config = ConfigDict(extra="forbid")

    mission_id: str
    total_claims: int
    verified_claims: int
    claims: list[EvidenceClaimDTO]
    conflicts: list[ClaimConflictDTO] = Field(default_factory=list)
    trace: dict[str, Any] | None = None


class ArtifactType(StrEnum):
    """The 5 primary deliverable categories in the Agent-X Artifact Center."""

    REPORT = "REPORT"  # Architectural, security, and verification reports
    DATASET = "DATASET"  # Structured JSON, CSV, benchmark scorecards
    PRESENTATION = "PRESENTATION"  # Slide decks and executive briefings
    SUMMARY = "SUMMARY"  # Outcome briefs and TL;DR deliverables
    EVIDENCE_PACKAGE = "EVIDENCE_PACKAGE"  # Cryptographic proof manifests & Merkle trees
    OTHER = "OTHER"


class ArtifactDTO(BaseModel):
    """Immutable deliverable or evidence artifact with generation and verification status."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    mission_id: str
    title: str
    filename: str
    artifact_type: str = "REPORT"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    generation_status: str = "GENERATED"  # "GENERATED" | "GENERATING" | "FAILED" | "PENDING"
    verification_status: str = "VERIFIED"  # "VERIFIED" | "PENDING_AUDIT" | "UNVERIFIED" | "FAILED"
    sha256: str
    size_bytes: int
    gcs_uri: str
    content: str | None = None
    content_type: str = "text/markdown"
    task_id: str | None = None
    agent_role: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreateArtifactRequest(BaseModel):
    """Payload to register a newly generated mission deliverable."""

    model_config = ConfigDict(extra="forbid")

    title: str
    filename: str
    artifact_type: str = "REPORT"
    content: str
    content_type: str = "text/markdown"
    task_id: str | None = None
    agent_role: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# --- 5. APPROVAL SCHEMAS ---


class ApprovalDecisionRequest(BaseModel):
    """Operator decision input for a pending approval."""

    model_config = ConfigDict(extra="forbid")

    decision_notes: str | None = Field(
        default=None, description="Explanation or manual feedback from operator"
    )


class ApprovalDecisionResponse(BaseModel):
    """Response returned upon resolving a pending approval."""

    model_config = ConfigDict(extra="forbid")

    approval_id: str
    mission_id: str
    status: str  # "APPROVED" | "REJECTED"
    decision_notes: str | None
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# --- 6. FAILURE CENTER & TIMELINE SCHEMAS ---


class FailureRecordDTO(BaseModel):
    """Diagnosed failure record with 7 core telemetry attributes and self-healing trace."""

    model_config = ConfigDict(extra="forbid")

    failure_id: str
    failure: str  # Error proposition / diagnostic message
    classification: str  # One of the 9 taxonomy categories
    affected_task_id: str
    affected_task_name: str
    assigned_agent: str
    recovery_strategy: str  # One of the 9 recovery strategies
    replacement: str  # Tool name, Agent persona, injected task, or modified params
    additional_resources: str  # Additional tokens, budget, or timeout grant
    result: str  # "RECOVERED" | "APPLIED" | "FAILED" | "ESCALATED_HITL" | "PENDING"
    retry_count: int = 0
    max_retries: int = 3
    is_recoverable: bool = True
    diagnostic_reasoning: str
    stack_trace: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TimelineEventDTO(BaseModel):
    """Unified chronological milestone or execution event in the mission lifecycle."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    timestamp: datetime
    event_type: str
    title: str
    description: str
    category: str  # "LIFECYCLE" | "TASK" | "FAILURE" | "RECOVERY" | "RESOURCE" | "EVIDENCE" | "DRIFT" | "APPROVAL"
    agent_role: str | None = None
    task_id: str | None = None
    severity: str = "INFO"  # "INFO" | "SUCCESS" | "WARNING" | "ERROR" | "CRITICAL"
    metadata: dict[str, Any] = Field(default_factory=dict)


class FailureCenterSummaryDTO(BaseModel):
    """Aggregated health and recovery statistics."""

    model_config = ConfigDict(extra="forbid")

    total_failures: int
    healed_count: int
    escalated_hitl_count: int
    recovery_rate: float
    categories_breakdown: dict[str, int] = Field(default_factory=dict)
    strategies_breakdown: dict[str, int] = Field(default_factory=dict)


class FailureCenterResponseDTO(BaseModel):
    """Complete Failure Center payload with 7 failure attributes and chronological mission timeline."""

    model_config = ConfigDict(extra="forbid")

    mission_id: str
    summary: FailureCenterSummaryDTO
    failures: list[FailureRecordDTO]
    timeline: list[TimelineEventDTO]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

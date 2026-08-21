"""Agent-X Unknowns Engine Data Models and Evaluation Schemas."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from agentx_common.schemas import AgentRole, EpistemicState


class PriorityTier(StrEnum):
    """Categorical ranking for an unknown's urgency and impact."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EpistemicUnknown(BaseModel):
    """Rich domain representation of an epistemic gap or unknown in the operating environment."""

    model_config = ConfigDict(extra="forbid")

    unknown_id: str = Field(default_factory=lambda: f"unk_{uuid4().hex[:10]}")
    mission_id: str
    question: str = Field(..., description="Concrete missing question or unobserved state")
    impact_description: str = Field(..., description="Why this unknown affects the mission")
    target_entity_id: str | None = Field(default=None, description="Related entity ID if any")

    # Core Assessment Dimensions [0.0, 1.0]
    impact: float = Field(default=0.5, ge=0.0, le=1.0, description="Severity of potential failure")
    uncertainty: float = Field(
        default=0.9, ge=0.0, le=1.0, description="Degree of epistemic entropy"
    )
    decision_relevance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How strongly this unknown dictates architecture/DAG paths",
    )
    research_cost: float = Field(
        default=0.2, ge=0.0, le=1.0, description="Estimated time/token cost to discover the answer"
    )
    urgency: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Time sensitivity and blocker severity"
    )

    # Workflow & Blocking State
    blocking_task_ids: list[str] = Field(default_factory=list)
    suggested_agent_role: AgentRole = Field(default=AgentRole.CODER)
    discovery_strategy: str = Field(
        default="INSPECT_ENVIRONMENT",
        description="Strategy to discover: e.g. CLI_COMMAND, API_QUERY, FILE_READ",
    )
    discovery_command: str | None = Field(
        default=None, description="Candidate command to execute if known"
    )

    is_resolved: bool = Field(default=False)
    resolved_fact_id: str | None = None
    epistemic_state: EpistemicState = Field(default=EpistemicState.CRITICAL_UNKNOWN)

    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None


class PriorityBreakdown(BaseModel):
    """Explainable transparent mathematical breakdown of priority score."""

    model_config = ConfigDict(extra="forbid")

    priority_score: float = Field(..., ge=0.0, le=100.0, description="Composite score 0-100")
    tier: PriorityTier
    weighted_impact: float
    weighted_uncertainty: float
    weighted_decision_relevance: float
    weighted_urgency: float
    cost_discount_bonus: float
    explanation: str = Field(..., description="Human-readable transparent justification")
    should_convert_to_task: bool


class PrioritizedUnknown(BaseModel):
    """An evaluated unknown paired with its explainable priority calculation."""

    model_config = ConfigDict(extra="forbid")

    unknown: EpistemicUnknown
    evaluation: PriorityBreakdown


class ConflictReport(BaseModel):
    """Report generated when conflicting evidence is detected between multiple facts."""

    model_config = ConfigDict(extra="forbid")

    conflict_id: str = Field(default_factory=lambda: f"cnf_{uuid4().hex[:10]}")
    mission_id: str
    entity_id: str | None = None
    subject: str
    predicate: str
    conflicting_fact_ids: list[str]
    conflicting_values: list[Any]
    detected_unknown: EpistemicUnknown
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

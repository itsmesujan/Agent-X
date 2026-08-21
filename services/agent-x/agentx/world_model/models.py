"""Agent-X World Model Core Domain Models and Epistemic Entities."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from agentx.goal_engine.schemas import RiskLevel
from agentx_common.schemas import AgentRole, EpistemicState


class EntityType(StrEnum):
    """Types of semantic entities in the operating environment."""

    REPOSITORY = "REPOSITORY"
    SOURCE_FILE = "SOURCE_FILE"
    CLOUD_SERVICE = "CLOUD_SERVICE"
    DATABASE_RESOURCE = "DATABASE_RESOURCE"
    SECRET_POINTER = "SECRET_POINTER"
    TEST_SUITE = "TEST_SUITE"
    ARTIFACT = "ARTIFACT"
    ENVIRONMENT_VARIABLE = "ENVIRONMENT_VARIABLE"
    API_ENDPOINT = "API_ENDPOINT"
    PACKAGE_DEPENDENCY = "PACKAGE_DEPENDENCY"
    GENERIC_RESOURCE = "GENERIC_RESOURCE"


class RelationshipType(StrEnum):
    """Semantic relationship types between entities, facts, and unknowns."""

    DEPENDS_ON = "DEPENDS_ON"
    MUTATES = "MUTATES"
    READS_FROM = "READS_FROM"
    AUTHENTICATES_VIA = "AUTHENTICATES_VIA"
    PRODUCES = "PRODUCES"
    BLOCKED_BY_UNKNOWN = "BLOCKED_BY_UNKNOWN"
    VERIFIES = "VERIFIES"
    CONSTRAINS = "CONSTRAINS"
    SUPERSEDES = "SUPERSEDES"
    INVALIDATES = "INVALIDATES"
    DERIVED_FROM = "DERIVED_FROM"


class SourceType(StrEnum):
    """Origin category for an observation, fact, or claim."""

    TOOL_EXECUTION = "TOOL_EXECUTION"
    FILE_CONTENT = "FILE_CONTENT"
    API_RESPONSE = "API_RESPONSE"
    USER_INPUT = "USER_INPUT"
    LLM_INFERENCE = "LLM_INFERENCE"
    VERIFICATION_PROOF = "VERIFICATION_PROOF"
    SYSTEM_INSPECTION = "SYSTEM_INSPECTION"


class SourceProvenance(BaseModel):
    """Cryptographic and contextual origin of a verified fact or observation."""

    model_config = ConfigDict(extra="forbid")

    source_type: SourceType
    source_ref: str = Field(..., description="URI, command string, file path, or API endpoint")
    task_id: str | None = Field(default=None, description="Task ID that produced this observation")
    agent_role: AgentRole | None = Field(
        default=None, description="Agent persona that collected evidence"
    )
    evidence_uri: str | None = Field(
        default=None, description="Immutable GCS URI of evidence artifact"
    )
    raw_evidence_hash: str | None = Field(
        default=None, description="SHA-256 hex digest of raw output payload"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Observation(BaseModel):
    """Raw empirical observation captured during task execution."""

    model_config = ConfigDict(extra="forbid")

    observation_id: str = Field(default_factory=lambda: f"obs_{uuid4().hex[:10]}")
    mission_id: str
    source: SourceProvenance
    raw_data: Any = Field(..., description="Raw output text, JSON dict, or exit code")
    summary: str = Field(..., description="Human-readable synthesis of the observation")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Fact(BaseModel):
    """An asserted property or state regarding an entity or the environment."""

    model_config = ConfigDict(extra="forbid")

    fact_id: str = Field(default_factory=lambda: f"fct_{uuid4().hex[:10]}")
    mission_id: str
    entity_id: str | None = Field(default=None, description="Target entity ID if entity-specific")
    subject: str = Field(..., description="Entity or topic name (e.g. 'Cloud Run agentx-api')")
    predicate: str = Field(..., description="Property asserted (e.g. 'ingress_setting')")
    value: Any = Field(..., description="Observed value (e.g. 'INTERNAL_AND_CLOUD_LOAD_BALANCING')")
    epistemic_state: EpistemicState = Field(default=EpistemicState.KNOWN_FACT)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: SourceProvenance
    observation_ids: list[str] = Field(
        default_factory=list, description="IDs of observations supporting this fact"
    )
    is_valid: bool = Field(default=True, description="False if invalidated or refuted")
    invalidated_at: datetime | None = None
    invalidated_reason: str | None = None
    superseded_by_fact_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Claim(BaseModel):
    """Hypothesis or working assumption formulated by an agent prior to empirical proof."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(default_factory=lambda: f"clm_{uuid4().hex[:10]}")
    mission_id: str
    entity_id: str | None = None
    statement: str = Field(..., description="Hypothesized claim statement")
    agent_role: AgentRole
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    epistemic_state: EpistemicState = Field(default=EpistemicState.INFERRED_ASSUMPTION)
    supporting_evidence_uris: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Unknown(BaseModel):
    """Epistemic gap or missing information requiring exploration or discovery."""

    model_config = ConfigDict(extra="forbid")

    unknown_id: str = Field(default_factory=lambda: f"unk_{uuid4().hex[:10]}")
    mission_id: str
    question: str = Field(..., description="The concrete missing question or unobserved state")
    impact: str = Field(..., description="Why this unknown blocks or influences the mission")
    epistemic_state: EpistemicState = Field(default=EpistemicState.CRITICAL_UNKNOWN)
    blocking_task_ids: list[str] = Field(
        default_factory=list, description="Tasks blocked by this unknown"
    )
    is_resolved: bool = Field(default=False)
    resolved_fact_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None


class Constraint(BaseModel):
    """Inviolable operational or architectural boundary for the mission."""

    model_config = ConfigDict(extra="forbid")

    constraint_id: str = Field(default_factory=lambda: f"cst_{uuid4().hex[:10]}")
    mission_id: str
    name: str
    rule_statement: str
    is_strict: bool = Field(default=True, description="Strict boundaries cannot be relaxed")
    enforced_by_entity_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Risk(BaseModel):
    """Identified security or operational hazard in the operating environment."""

    model_config = ConfigDict(extra="forbid")

    risk_id: str = Field(default_factory=lambda: f"rsk_{uuid4().hex[:10]}")
    mission_id: str
    entity_id: str | None = None
    title: str
    description: str
    severity: RiskLevel = Field(default=RiskLevel.MEDIUM)
    mitigation_strategy: str | None = None
    is_mitigated: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WorldModelEntity(BaseModel):
    """Semantic graph node representing an environmental entity."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., description="Unique entity identifier (e.g. 'repo:agent-x')")
    mission_id: str
    entity_type: EntityType
    name: str
    properties: dict[str, Any] = Field(default_factory=dict)
    epistemic_state: EpistemicState = Field(default=EpistemicState.KNOWN_FACT)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_uri: str | None = Field(default=None, description="GCS URI proving entity existence")
    source: SourceProvenance | None = None
    created_by_task_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RelationshipEdge(BaseModel):
    """Semantic directed edge between two nodes in the World Model graph."""

    model_config = ConfigDict(extra="forbid")

    edge_id: str = Field(default_factory=lambda: f"edg_{uuid4().hex[:10]}")
    mission_id: str
    source_id: str = Field(..., description="Origin node ID (entity, fact, claim, or unknown)")
    target_id: str = Field(..., description="Destination node ID")
    relationship: RelationshipType
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

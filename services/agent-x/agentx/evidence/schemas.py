"""Agent-X Evidence Engine Schemas, Claims, and Trace Models."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ClaimStatus(StrEnum):
    """Lifecycle and verification state of an empirical claim."""

    PROPOSED = "PROPOSED"
    VERIFIED = "VERIFIED"
    REFUTED = "REFUTED"
    INVALIDATED = "INVALIDATED"
    SUPERSEDED = "SUPERSEDED"


class SourceReliability(StrEnum):
    """Credibility tier assigned to an information source."""

    AUTHORITATIVE = "AUTHORITATIVE"  # 1.0 (Official system state, compiler, tests)
    PRIMARY_EVIDENCE = "PRIMARY_EVIDENCE"  # 0.9 (Tool execution output, direct API response)
    SECONDARY_DOCS = "SECONDARY_DOCS"  # 0.75 (Reference docs, structured spec files)
    HEURISTIC_INFERENCE = "HEURISTIC_INFERENCE"  # 0.5 (LLM assumption, heuristic deduction)
    UNTRUSTED_WEB = "UNTRUSTED_WEB"  # 0.3 (Unsanitized third-party web content)


class EvidenceItem(BaseModel):
    """Immutable evidence artifact with cryptographic hash and origin attribution."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(default_factory=lambda: f"evd_{uuid4().hex[:10]}")
    source_uri: str = Field(
        ..., description="URI, path, or API endpoint where evidence was captured"
    )
    content_ref: str = Field(..., description="Short summary snippet or content reference")
    raw_data_hash: str = Field(..., description="SHA-256 digest of the raw evidence payload")
    byte_size: int = Field(default=0, ge=0, description="Byte size of raw evidence payload")
    collected_by_agent: str | None = Field(
        default=None, description="Agent persona that captured evidence"
    )
    task_id: str | None = Field(default=None, description="Task ID that generated evidence")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Contextual headers and execution metadata"
    )


class EvidenceClaim(BaseModel):
    """Structured empirical claim with source attribution, reliability, and lifecycle status."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(default_factory=lambda: f"clm_{uuid4().hex[:10]}")
    mission_id: str
    statement: str = Field(..., description="Human and LLM readable claim proposition")
    subject: str = Field(..., description="Entity or topic of the claim (e.g. 'Database')")
    predicate: str = Field(..., description="Property asserted (e.g. 'schema_version')")
    value: Any = Field(..., description="Asserted value (e.g. 2)")
    source_ref: str = Field(..., description="Origin source reference URI or command")
    source_reliability: SourceReliability = Field(default=SourceReliability.PRIMARY_EVIDENCE)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence score")
    status: ClaimStatus = Field(default=ClaimStatus.PROPOSED)
    content_ref: str = Field(default="", description="Snippet or pointer to supporting content")
    evidence_items: list[EvidenceItem] = Field(
        default_factory=list, description="Attached evidence proofs"
    )
    conflict_ids: list[str] = Field(default_factory=list, description="IDs of contradictory claims")
    invalidation_reason: str | None = Field(
        default=None, description="Reason if claim was refuted/invalidated"
    )
    superseded_by_claim_id: str | None = Field(
        default=None, description="Newer claim ID that replaces this"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    verified_at: datetime | None = Field(default=None)


class ClaimConflict(BaseModel):
    """Contradiction or disagreement detected between two claims."""

    model_config = ConfigDict(extra="forbid")

    conflict_id: str = Field(default_factory=lambda: f"cfl_{uuid4().hex[:10]}")
    claim_a_id: str
    claim_b_id: str
    subject: str
    predicate: str
    value_a: Any
    value_b: Any
    reason: str
    severity: str = Field(default="MODERATE", description="CRITICAL | MODERATE | MINOR")
    is_resolved: bool = Field(default=False)
    resolution_notes: str | None = None
    resolved_at: datetime | None = None


class EvidenceTraceNode(BaseModel):
    """Node in an explainable evidence provenance graph."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str
    statement: str
    confidence: float
    source_reliability: SourceReliability
    status: ClaimStatus
    evidence_hashes: list[str]
    source_refs: list[str]
    is_verified: bool


class EvidenceTrace(BaseModel):
    """Complete cryptographic and explainable evidence trace for a final recommendation."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(default_factory=lambda: f"trc_{uuid4().hex[:10]}")
    mission_id: str
    recommendation: str = Field(
        ..., description="Actionable proposal or deliverable recommendation"
    )
    overall_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Aggregated confidence score"
    )
    claim_nodes: list[EvidenceTraceNode] = Field(default_factory=list)
    root_claim_ids: list[str] = Field(default_factory=list)
    conflicts_evaluated: list[ClaimConflict] = Field(default_factory=list)
    cryptographic_root_hash: str = Field(
        ..., description="Merkle/SHA-256 root hash of all underlying evidence"
    )
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

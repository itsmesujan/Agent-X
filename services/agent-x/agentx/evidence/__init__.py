"""Agent-X Evidence Engine Package."""

from agentx.evidence.engine import ClaimNotFoundError, EvidenceEngine
from agentx.evidence.ranking import compute_source_credibility_score, rank_claims
from agentx.evidence.schemas import (
    ClaimConflict,
    ClaimStatus,
    EvidenceClaim,
    EvidenceItem,
    EvidenceTrace,
    EvidenceTraceNode,
    SourceReliability,
)

__all__ = [
    "ClaimStatus",
    "SourceReliability",
    "EvidenceItem",
    "EvidenceClaim",
    "ClaimConflict",
    "EvidenceTraceNode",
    "EvidenceTrace",
    "compute_source_credibility_score",
    "rank_claims",
    "EvidenceEngine",
    "ClaimNotFoundError",
]

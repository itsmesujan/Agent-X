"""Agent-X Source and Claim Credibility Ranking Calculator."""

import math
from datetime import UTC, datetime

from agentx.evidence.schemas import EvidenceClaim, SourceReliability

RELIABILITY_WEIGHTS: dict[SourceReliability, float] = {
    SourceReliability.AUTHORITATIVE: 1.00,
    SourceReliability.PRIMARY_EVIDENCE: 0.90,
    SourceReliability.SECONDARY_DOCS: 0.75,
    SourceReliability.HEURISTIC_INFERENCE: 0.50,
    SourceReliability.UNTRUSTED_WEB: 0.30,
}


def compute_source_credibility_score(
    reliability: SourceReliability,
    evidence_count: int = 1,
    created_at: datetime | None = None,
    half_life_hours: float = 24.0,
) -> float:
    """Calculates a normalized credibility score (0.0 to 1.0) incorporating source authority, corroboration, and freshness."""
    base_weight = RELIABILITY_WEIGHTS.get(reliability, 0.5)

    # Corroboration bonus: up to +0.15 for multiple independent evidence proofs
    corroboration_bonus = min(0.15, max(0, evidence_count - 1) * 0.05)

    # Freshness factor (exponential decay)
    freshness_factor = 1.0
    if created_at is not None:
        now = datetime.now(UTC)
        age_hours = max(0.0, (now - created_at).total_seconds() / 3600.0)
        # Exponential half-life decay
        freshness_factor = math.exp(-0.693 * (age_hours / half_life_hours))
        # Clamp freshness so historical authoritative facts don't drop below 0.75
        freshness_factor = max(0.75, freshness_factor)

    score = (base_weight + corroboration_bonus) * freshness_factor
    return round(min(1.0, max(0.0, score)), 4)


def rank_claims(claims: list[EvidenceClaim]) -> list[EvidenceClaim]:
    """Sorts claims in descending order of composite credibility score."""
    return sorted(
        claims,
        key=lambda c: compute_source_credibility_score(
            reliability=c.source_reliability,
            evidence_count=len(c.evidence_items),
            created_at=c.created_at,
        ),
        reverse=True,
    )

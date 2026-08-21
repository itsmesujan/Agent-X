"""Agent-X Evidence Engine for Managing Claims, Verification Proofs, and Evidence Traces."""

import hashlib
import threading
from datetime import UTC, datetime
from typing import Any

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


class ClaimNotFoundError(Exception):
    """Raised when a referenced claim is not found."""

    def __init__(self, claim_id: str) -> None:
        super().__init__(f"Claim with ID '{claim_id}' was not found in EvidenceEngine")


class EvidenceEngine:
    """Thread-safe engine for managing empirical claims, attaching evidence proofs, and generating cryptographic traces."""

    def __init__(self) -> None:
        self._claims: dict[str, EvidenceClaim] = {}
        self._conflicts: dict[str, ClaimConflict] = {}
        self._lock = threading.Lock()

    # --- 1. CLAIM CREATION ---

    def create_claim(
        self,
        mission_id: str,
        statement: str,
        subject: str,
        predicate: str,
        value: Any,
        source_ref: str,
        source_reliability: SourceReliability = SourceReliability.PRIMARY_EVIDENCE,
        confidence: float = 0.8,
        content_ref: str = "",
        claim_id: str | None = None,
    ) -> EvidenceClaim:
        """Creates and indexes a new empirical claim, automatically executing conflict checks."""
        claim = EvidenceClaim(
            claim_id=claim_id
            or f"clm_{hashlib.sha256(f'{subject}:{predicate}:{value}'.encode()).hexdigest()[:10]}",
            mission_id=mission_id,
            statement=statement,
            subject=subject,
            predicate=predicate,
            value=value,
            source_ref=source_ref,
            source_reliability=source_reliability,
            confidence=min(1.0, max(0.0, confidence)),
            status=ClaimStatus.PROPOSED,
            content_ref=content_ref,
        )

        with self._lock:
            self._claims[claim.claim_id] = claim
            # Run conflict detection
            self._detect_conflicts_internal(claim)

        return claim

    # --- 2. EVIDENCE ATTACHMENT ---

    def attach_evidence(
        self,
        claim_id: str,
        content: str | bytes,
        source_uri: str,
        content_ref: str = "",
        task_id: str | None = None,
        agent_role: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceItem:
        """Attaches a cryptographically hashed evidence proof to an existing claim."""
        content_bytes = content.encode("utf-8") if isinstance(content, str) else content
        sha256_hash = hashlib.sha256(content_bytes).hexdigest()

        evidence_item = EvidenceItem(
            source_uri=source_uri,
            content_ref=content_ref or (content_bytes[:100].decode("utf-8", errors="ignore")),
            raw_data_hash=sha256_hash,
            byte_size=len(content_bytes),
            collected_by_agent=agent_role,
            task_id=task_id,
            metadata=metadata or {},
        )

        with self._lock:
            if claim_id not in self._claims:
                raise ClaimNotFoundError(claim_id)
            claim = self._claims[claim_id]
            claim.evidence_items.append(evidence_item)

            # Re-evaluate confidence with corroboration bonus
            updated_score = compute_source_credibility_score(
                reliability=claim.source_reliability,
                evidence_count=len(claim.evidence_items),
                created_at=claim.created_at,
            )
            claim.confidence = updated_score
            claim.updated_at = datetime.now(UTC)

        return evidence_item

    # --- 3. CONFLICT DETECTION ---

    def _detect_conflicts_internal(self, new_claim: EvidenceClaim) -> list[ClaimConflict]:
        """Scans existing active claims for contradictory property values."""
        detected: list[ClaimConflict] = []

        for existing_id, existing_claim in self._claims.items():
            if existing_id == new_claim.claim_id:
                continue
            if existing_claim.mission_id != new_claim.mission_id:
                continue
            if existing_claim.status in (
                ClaimStatus.INVALIDATED,
                ClaimStatus.REFUTED,
                ClaimStatus.SUPERSEDED,
            ):
                continue

            # Same entity subject and predicate, but differing values
            if (
                existing_claim.subject.lower() == new_claim.subject.lower()
                and existing_claim.predicate.lower() == new_claim.predicate.lower()
                and existing_claim.value != new_claim.value
            ):
                conflict = ClaimConflict(
                    claim_a_id=existing_id,
                    claim_b_id=new_claim.claim_id,
                    subject=new_claim.subject,
                    predicate=new_claim.predicate,
                    value_a=existing_claim.value,
                    value_b=new_claim.value,
                    reason=(
                        f"Contradiction on '{new_claim.subject}.{new_claim.predicate}': "
                        f"'{existing_claim.value}' vs '{new_claim.value}'"
                    ),
                    severity="CRITICAL" if isinstance(new_claim.value, bool) else "MODERATE",
                )
                self._conflicts[conflict.conflict_id] = conflict
                existing_claim.conflict_ids.append(conflict.conflict_id)
                new_claim.conflict_ids.append(conflict.conflict_id)
                detected.append(conflict)

        return detected

    def get_conflicts(self, unresolved_only: bool = True) -> list[ClaimConflict]:
        """Return registered claim conflicts."""
        with self._lock:
            if unresolved_only:
                return [c for c in self._conflicts.values() if not c.is_resolved]
            return list(self._conflicts.values())

    def resolve_conflict(
        self,
        conflict_id: str,
        winning_claim_id: str,
        resolution_notes: str,
    ) -> ClaimConflict:
        """Resolves a conflict by validating the winning claim and invalidating the conflicting claim."""
        with self._lock:
            if conflict_id not in self._conflicts:
                raise ValueError(f"Conflict '{conflict_id}' was not found")
            conflict = self._conflicts[conflict_id]

            losing_id = (
                conflict.claim_b_id
                if winning_claim_id == conflict.claim_a_id
                else conflict.claim_a_id
            )

            # Invalidate losing claim
            if losing_id in self._claims:
                losing_claim = self._claims[losing_id]
                losing_claim.status = ClaimStatus.REFUTED
                losing_claim.invalidation_reason = (
                    f"Refuted by conflict resolution: {resolution_notes}"
                )
                losing_claim.superseded_by_claim_id = winning_claim_id

            conflict.is_resolved = True
            conflict.resolution_notes = resolution_notes
            conflict.resolved_at = datetime.now(UTC)

            return conflict

    # --- 4. CLAIM VERIFICATION ---

    def verify_claim(
        self,
        claim_id: str,
        verifier_agent: str | None = None,
        minimum_confidence: float = 0.6,
    ) -> EvidenceClaim:
        """Verifies a claim when it satisfies evidence backing and conflict resolution standards."""
        with self._lock:
            if claim_id not in self._claims:
                raise ClaimNotFoundError(claim_id)
            claim = self._claims[claim_id]

            if claim.status in (ClaimStatus.INVALIDATED, ClaimStatus.REFUTED):
                raise ValueError(f"Cannot verify {claim.status.value} claim '{claim_id}'")

            if not claim.evidence_items:
                raise ValueError(f"Claim '{claim_id}' has no attached evidence items")

            # Check for unresolved critical conflicts
            unresolved_conflicts = [
                self._conflicts[cid]
                for cid in claim.conflict_ids
                if cid in self._conflicts and not self._conflicts[cid].is_resolved
            ]
            if any(c.severity == "CRITICAL" for c in unresolved_conflicts):
                raise ValueError(f"Claim '{claim_id}' has unresolved critical conflicts")

            if claim.confidence < minimum_confidence:
                raise ValueError(
                    f"Claim confidence {claim.confidence:.2f} is below minimum threshold {minimum_confidence:.2f}"
                )

            claim.status = ClaimStatus.VERIFIED
            claim.verified_at = datetime.now(UTC)
            claim.updated_at = datetime.now(UTC)
            return claim

    # --- 5. CLAIM INVALIDATION ---

    def invalidate_claim(
        self,
        claim_id: str,
        reason: str,
        superseded_by_claim_id: str | None = None,
    ) -> EvidenceClaim:
        """Invalidates or supersedes an empirical claim with documented justification."""
        with self._lock:
            if claim_id not in self._claims:
                raise ClaimNotFoundError(claim_id)
            claim = self._claims[claim_id]

            claim.status = (
                ClaimStatus.SUPERSEDED if superseded_by_claim_id else ClaimStatus.INVALIDATED
            )
            claim.invalidation_reason = reason
            claim.superseded_by_claim_id = superseded_by_claim_id
            claim.updated_at = datetime.now(UTC)
            return claim

    # --- 6. SOURCE RANKING & QUERY ---

    def get_claim(self, claim_id: str) -> EvidenceClaim:
        """Retrieve a claim by ID."""
        with self._lock:
            if claim_id not in self._claims:
                raise ClaimNotFoundError(claim_id)
            return self._claims[claim_id]

    def list_claims(
        self,
        mission_id: str | None = None,
        status: ClaimStatus | None = None,
        subject: str | None = None,
    ) -> list[EvidenceClaim]:
        """List claims matching criteria, ordered by credibility score."""
        with self._lock:
            candidates = list(self._claims.values())

        filtered: list[EvidenceClaim] = []
        for c in candidates:
            if mission_id and c.mission_id != mission_id:
                continue
            if status and c.status != status:
                continue
            if subject and c.subject.lower() != subject.lower():
                continue
            filtered.append(c)

        return rank_claims(filtered)

    # --- 7. EVIDENCE TRACE FOR RECOMMENDATIONS ---

    def build_evidence_trace(
        self,
        mission_id: str,
        recommendation: str,
        supporting_claim_ids: list[str],
    ) -> EvidenceTrace:
        """Constructs an explainable and cryptographically anchored evidence trace for a final recommendation."""
        nodes: list[EvidenceTraceNode] = []
        all_hashes: list[str] = []
        conflicts: list[ClaimConflict] = []

        with self._lock:
            for cid in supporting_claim_ids:
                if cid not in self._claims:
                    continue
                claim = self._claims[cid]
                hashes = [e.raw_data_hash for e in claim.evidence_items]
                all_hashes.extend(hashes)

                nodes.append(
                    EvidenceTraceNode(
                        claim_id=claim.claim_id,
                        statement=claim.statement,
                        confidence=claim.confidence,
                        source_reliability=claim.source_reliability,
                        status=claim.status,
                        evidence_hashes=hashes,
                        source_refs=[claim.source_ref]
                        + [e.source_uri for e in claim.evidence_items],
                        is_verified=claim.status == ClaimStatus.VERIFIED,
                    )
                )

                for conf_id in claim.conflict_ids:
                    if conf_id in self._conflicts and self._conflicts[conf_id] not in conflicts:
                        conflicts.append(self._conflicts[conf_id])

        # Compute aggregate confidence
        if nodes:
            avg_confidence = sum(n.confidence for n in nodes) / len(nodes)
        else:
            avg_confidence = 0.5

        # Compute cryptographic Merkle root hash of all evidence
        combined_payload = ":".join(sorted(all_hashes) if all_hashes else supporting_claim_ids)
        root_hash = hashlib.sha256(f"{recommendation}:{combined_payload}".encode()).hexdigest()

        return EvidenceTrace(
            mission_id=mission_id,
            recommendation=recommendation,
            overall_confidence=round(avg_confidence, 4),
            claim_nodes=nodes,
            root_claim_ids=supporting_claim_ids,
            conflicts_evaluated=conflicts,
            cryptographic_root_hash=root_hash,
        )

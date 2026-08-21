"""Unit tests for Agent-X Evidence Engine, Claims, Source Ranking, and Traceability."""

import pytest

from agentx.evidence import (
    ClaimStatus,
    EvidenceClaim,
    EvidenceEngine,
    SourceReliability,
    compute_source_credibility_score,
    rank_claims,
)


def test_claim_creation_and_attributes() -> None:
    """Test claim creation with all mandatory metadata fields."""
    engine = EvidenceEngine()

    claim = engine.create_claim(
        mission_id="msn_evd_01",
        statement="Cloud Run concurrency is configured to 80 requests per container instance",
        subject="Cloud Run agentx-api",
        predicate="concurrency",
        value=80,
        source_ref="gcloud run services describe agentx-api --format=json",
        source_reliability=SourceReliability.AUTHORITATIVE,
        confidence=0.95,
        content_ref="concurrency: 80",
    )

    assert claim.claim_id.startswith("clm_")
    assert claim.mission_id == "msn_evd_01"
    assert claim.subject == "Cloud Run agentx-api"
    assert claim.predicate == "concurrency"
    assert claim.value == 80
    assert claim.source_ref.startswith("gcloud run")
    assert claim.source_reliability == SourceReliability.AUTHORITATIVE
    assert claim.confidence == 0.95
    assert claim.status == ClaimStatus.PROPOSED
    assert claim.created_at is not None
    assert claim.content_ref == "concurrency: 80"


def test_evidence_attachment_and_sha256_hash() -> None:
    """Test attaching evidence with cryptographic hash and corroboration score update."""
    engine = EvidenceEngine()

    claim = engine.create_claim(
        mission_id="msn_evd_01",
        statement="Firestore collection missions is partitioned by tenant_id",
        subject="Firestore",
        predicate="partitioning",
        value="tenant_id",
        source_ref="firestore.rules",
        source_reliability=SourceReliability.PRIMARY_EVIDENCE,
    )

    raw_output = '{"partitionKey": "tenant_id", "status": "ACTIVE"}'
    evidence = engine.attach_evidence(
        claim_id=claim.claim_id,
        content=raw_output,
        source_uri="gs://agentx-evidence/missions/msn_evd_01/tasks/task_01/firestore_spec.json",
        content_ref="partitionKey: tenant_id",
        task_id="task_01",
        agent_role="DEVOPS",
    )

    assert len(evidence.raw_data_hash) == 64  # Valid SHA-256 hex string
    assert evidence.byte_size == len(raw_output.encode("utf-8"))
    assert len(claim.evidence_items) == 1
    assert claim.evidence_items[0].raw_data_hash == evidence.raw_data_hash

    # Attach second piece of evidence (corroboration boost)
    orig_confidence = claim.confidence
    engine.attach_evidence(
        claim_id=claim.claim_id,
        content="Verified partitioning in terraform main.tf",
        source_uri="gs://agentx-evidence/missions/msn_evd_01/tasks/task_02/main.tf",
    )
    assert len(claim.evidence_items) == 2
    assert claim.confidence >= orig_confidence


def test_source_ranking_and_credibility() -> None:
    """Test quantitative source credibility ranking calculation."""
    auth_score = compute_source_credibility_score(SourceReliability.AUTHORITATIVE, evidence_count=1)
    untrusted_score = compute_source_credibility_score(
        SourceReliability.UNTRUSTED_WEB, evidence_count=1
    )

    assert auth_score > untrusted_score
    assert auth_score >= 0.95
    assert untrusted_score <= 0.35

    # Test rank_claims
    c_low = EvidenceClaim(
        mission_id="msn_evd_01",
        statement="Low claim",
        subject="S1",
        predicate="P1",
        value=1,
        source_ref="blog.com",
        source_reliability=SourceReliability.UNTRUSTED_WEB,
    )
    c_high = EvidenceClaim(
        mission_id="msn_evd_01",
        statement="High claim",
        subject="S2",
        predicate="P2",
        value=2,
        source_ref="official.gov",
        source_reliability=SourceReliability.AUTHORITATIVE,
    )

    ranked = rank_claims([c_low, c_high])
    assert ranked[0].statement == "High claim"
    assert ranked[1].statement == "Low claim"


def test_conflict_detection_and_resolution() -> None:
    """Test automated contradiction detection and resolution."""
    engine = EvidenceEngine()

    # Claim A: VPC connector is enabled
    claim_a = engine.create_claim(
        mission_id="msn_evd_01",
        statement="VPC Connector is enabled",
        subject="Cloud Run agentx-api",
        predicate="vpc_connector_enabled",
        value=True,
        source_ref="terraform/main.tf",
        source_reliability=SourceReliability.PRIMARY_EVIDENCE,
    )

    # Claim B: VPC connector is disabled (Contradiction!)
    claim_b = engine.create_claim(
        mission_id="msn_evd_01",
        statement="VPC Connector is disabled",
        subject="Cloud Run agentx-api",
        predicate="vpc_connector_enabled",
        value=False,
        source_ref="gcloud run services describe agentx-api",
        source_reliability=SourceReliability.AUTHORITATIVE,
    )

    # Verify conflict was automatically detected
    conflicts = engine.get_conflicts(unresolved_only=True)
    assert len(conflicts) == 1
    conf = conflicts[0]
    assert conf.severity == "CRITICAL"
    assert conf.subject == "Cloud Run agentx-api"
    assert conf.predicate == "vpc_connector_enabled"
    assert claim_a.claim_id in [conf.claim_a_id, conf.claim_b_id]
    assert claim_b.claim_id in [conf.claim_a_id, conf.claim_b_id]

    # Resolve conflict in favor of authoritative Claim B
    engine.resolve_conflict(
        conflict_id=conf.conflict_id,
        winning_claim_id=claim_b.claim_id,
        resolution_notes="Live gcloud inspection overrides local terraform draft",
    )

    # Verify losing claim is REFUTED
    assert claim_a.status == ClaimStatus.REFUTED
    assert "Live gcloud inspection" in (claim_a.invalidation_reason or "")
    assert len(engine.get_conflicts(unresolved_only=True)) == 0


def test_claim_verification_workflow() -> None:
    """Test verifying a claim with attached evidence proofs."""
    engine = EvidenceEngine()

    claim = engine.create_claim(
        mission_id="msn_evd_01",
        statement="Secret Manager permissions are properly scoped",
        subject="IAM",
        predicate="secret_accessor_role",
        value="roles/secretmanager.secretAccessor",
        source_ref="gcloud projects get-iam-policy",
        source_reliability=SourceReliability.AUTHORITATIVE,
        confidence=0.9,
    )

    # Verification should fail without evidence
    with pytest.raises(ValueError, match="no attached evidence"):
        engine.verify_claim(claim.claim_id)

    # Attach evidence
    engine.attach_evidence(
        claim_id=claim.claim_id,
        content="bindings: [{role: roles/secretmanager.secretAccessor, members: [serviceAccount:sa@dev]}]",
        source_uri="gs://agentx-evidence/iam_policy.yaml",
    )

    # Verification should now succeed
    verified_claim = engine.verify_claim(claim.claim_id)
    assert verified_claim.status == ClaimStatus.VERIFIED
    assert verified_claim.verified_at is not None


def test_claim_invalidation() -> None:
    """Test invalidating and superseding claims."""
    engine = EvidenceEngine()

    claim = engine.create_claim(
        mission_id="msn_evd_01",
        statement="API rate limit is 100 req/min",
        subject="API Gateway",
        predicate="rate_limit",
        value=100,
        source_ref="old_spec.md",
    )

    # Invalidate
    engine.invalidate_claim(
        claim_id=claim.claim_id,
        reason="Rate limit updated to 500 req/min in v2 config",
        superseded_by_claim_id="clm_v2_new",
    )

    assert claim.status == ClaimStatus.SUPERSEDED
    assert claim.invalidation_reason == "Rate limit updated to 500 req/min in v2 config"
    assert claim.superseded_by_claim_id == "clm_v2_new"


def test_evidence_trace_for_final_recommendations() -> None:
    """Test generating a cryptographic evidence trace for a final recommendation deliverable."""
    engine = EvidenceEngine()

    # Claim 1: Database ready
    c1 = engine.create_claim(
        mission_id="msn_evd_01",
        statement="Firestore native mode is initialized in us-central1",
        subject="Firestore",
        predicate="status",
        value="READY",
        source_ref="gcloud firestore databases describe",
        source_reliability=SourceReliability.AUTHORITATIVE,
    )
    engine.attach_evidence(
        claim_id=c1.claim_id,
        content='{"locationId": "us-central1", "type": "FIRESTORE_NATIVE", "state": "READY"}',
        source_uri="gs://agentx-evidence/firestore_state.json",
    )
    engine.verify_claim(c1.claim_id)

    # Claim 2: Security rules compiled
    c2 = engine.create_claim(
        mission_id="msn_evd_01",
        statement="Firestore security rules compiled with 0 errors",
        subject="Firestore Security Rules",
        predicate="compilation",
        value="SUCCESS",
        source_ref="firebase deploy --only firestore:rules",
        source_reliability=SourceReliability.AUTHORITATIVE,
    )
    engine.attach_evidence(
        claim_id=c2.claim_id,
        content="Rules compiled successfully. 0 syntax errors.",
        source_uri="gs://agentx-evidence/rules_compile.log",
    )
    engine.verify_claim(c2.claim_id)

    # Build evidence trace for final recommendation
    recommendation_text = "Deploy Cloud Run API workers connected to production Firestore instance"
    trace = engine.build_evidence_trace(
        mission_id="msn_evd_01",
        recommendation=recommendation_text,
        supporting_claim_ids=[c1.claim_id, c2.claim_id],
    )

    assert trace.trace_id.startswith("trc_")
    assert trace.mission_id == "msn_evd_01"
    assert trace.recommendation == recommendation_text
    assert trace.overall_confidence > 0.85
    assert len(trace.claim_nodes) == 2
    assert trace.claim_nodes[0].is_verified is True
    assert trace.claim_nodes[1].is_verified is True
    assert len(trace.claim_nodes[0].evidence_hashes) == 1
    assert len(trace.claim_nodes[1].evidence_hashes) == 1
    # Verify cryptographic root hash exists and is 64-char SHA-256
    assert len(trace.cryptographic_root_hash) == 64

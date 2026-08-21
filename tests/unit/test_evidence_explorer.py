"""Unit and integration tests for Agent-X Evidence Explorer backend and API endpoints."""

import hashlib

import pytest
from fastapi.testclient import TestClient

from agentx.api.state import state_manager
from agentx.evidence.engine import EvidenceEngine
from agentx.evidence.schemas import ClaimStatus, SourceReliability
from agentx.main import app


@pytest.fixture
def evidence_engine() -> EvidenceEngine:
    """Fixture providing a clean EvidenceEngine."""
    return EvidenceEngine()


def test_evidence_explorer_claim_creation_and_evidence_attachment(
    evidence_engine: EvidenceEngine,
) -> None:
    """Verify claim creation, stored evidence attachment, and dynamic credibility scoring."""
    mission_id = "msn_evidence_001"
    claim = evidence_engine.create_claim(
        mission_id=mission_id,
        statement="Database schema version is 2.0 with strict foreign key constraints.",
        subject="Database",
        predicate="schema_version",
        value=2.0,
        source_ref="alembic/versions/v2_0.py",
        source_reliability=SourceReliability.PRIMARY_EVIDENCE,
        confidence=0.85,
        content_ref="Revision ID: v2_0, Down Revision: v1_0",
    )

    assert claim.statement.startswith("Database schema version is 2.0")
    assert claim.subject == "Database"
    assert claim.predicate == "schema_version"
    assert claim.value == 2.0
    assert claim.status == ClaimStatus.PROPOSED
    assert len(claim.evidence_items) == 0

    # Attach immutable stored evidence artifact
    raw_migration_log = "INFO: Target database is up to date at revision v2_0."
    item = evidence_engine.attach_evidence(
        claim_id=claim.claim_id,
        content=raw_migration_log,
        source_uri="gs://agentx-evidence/missions/msn_001/migrations.log",
        content_ref=raw_migration_log[:60],
        task_id="task_migration_check",
        agent_role="DevOps",
    )

    assert item.source_uri == "gs://agentx-evidence/missions/msn_001/migrations.log"
    assert item.raw_data_hash == hashlib.sha256(raw_migration_log.encode()).hexdigest()
    assert item.collected_by_agent == "DevOps"
    assert len(claim.evidence_items) == 1
    assert claim.confidence >= 0.85


def test_evidence_explorer_conflict_detection_and_resolution(
    evidence_engine: EvidenceEngine,
) -> None:
    """Verify contradiction detection across opposing claims and explainable resolution."""
    mission_id = "msn_evidence_002"

    # Claim A: Port is 8080
    claim_a = evidence_engine.create_claim(
        mission_id=mission_id,
        statement="Server listening port is 8080.",
        subject="Server",
        predicate="port",
        value=8080,
        source_ref="config.yaml",
        source_reliability=SourceReliability.SECONDARY_DOCS,
    )

    # Claim B: Port is 9000 (contradiction)
    claim_b = evidence_engine.create_claim(
        mission_id=mission_id,
        statement="Server listening port is 9000.",
        subject="Server",
        predicate="port",
        value=9000,
        source_ref="netstat -tuln output",
        source_reliability=SourceReliability.AUTHORITATIVE,
    )

    conflicts = evidence_engine.get_conflicts(unresolved_only=True)
    assert len(conflicts) == 1
    assert conflicts[0].subject == "Server"
    assert conflicts[0].predicate == "port"
    assert conflicts[0].value_a == 8080
    assert conflicts[0].value_b == 9000
    assert conflicts[0].is_resolved is False

    assert conflicts[0].conflict_id in claim_a.conflict_ids
    assert conflicts[0].conflict_id in claim_b.conflict_ids

    # Resolve conflict in favor of Claim B (Authoritative source)
    resolved_conflict = evidence_engine.resolve_conflict(
        conflict_id=conflicts[0].conflict_id,
        winning_claim_id=claim_b.claim_id,
        resolution_notes="Live netstat verification proved port 9000 is active listener.",
    )

    assert resolved_conflict.is_resolved is True
    assert claim_a.status == ClaimStatus.REFUTED
    assert "Live netstat verification proved" in (claim_a.invalidation_reason or "")
    assert claim_a.superseded_by_claim_id == claim_b.claim_id


def test_api_evidence_explorer_endpoints() -> None:
    """Verify FastAPI GET /missions/{id}/evidence and GET /missions/{id}/evidence/claims/{id}."""
    client = TestClient(app)
    headers = {"Authorization": "Bearer dev-token-auditor"}

    # 1. Create a mission and seed evidence
    mission = state_manager.create_mission(
        title="Evidence Explorer Verification Mission",
        goal_statement="Validate evidence trace and decision reasoning.",
    )
    mission_id = mission.mission_id

    ee = state_manager.get_evidence_engine(mission_id)
    assert ee is not None
    claim = ee.create_claim(
        mission_id=mission_id,
        statement="Terraform configuration passed security audit with 0 findings.",
        subject="Terraform",
        predicate="security_audit_passed",
        value=True,
        source_ref="tfsec output",
        source_reliability=SourceReliability.PRIMARY_EVIDENCE,
        confidence=0.92,
        content_ref="0 potential problems detected.",
    )

    raw_proof = '{"results": [], "passed_rules": 42, "critical_failures": 0}'
    ee.attach_evidence(
        claim_id=claim.claim_id,
        content=raw_proof,
        source_uri="gs://agentx-evidence/missions/test/tfsec.json",
        content_ref="0 potential problems detected.",
        agent_role="Auditor",
        task_id="task_audit_001",
    )
    ee.verify_claim(claim.claim_id)

    # 2. Call GET /missions/{mission_id}/evidence
    resp = client.get(f"/api/v1/missions/{mission_id}/evidence", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["mission_id"] == mission_id
    assert data["total_claims"] == 1
    assert data["verified_claims"] == 1
    assert len(data["claims"]) == 1

    claim_dto = data["claims"][0]
    assert claim_dto["claim_id"] == claim.claim_id
    assert claim_dto["statement"].startswith("Terraform configuration passed")
    assert claim_dto["status"] == "VERIFIED"
    assert (
        "Certified as verified: Backed by 1 stored evidence artifact(s)"
        in claim_dto["final_decision_reason"]
    )
    assert len(claim_dto["evidence_items"]) == 1
    assert (
        claim_dto["evidence_items"][0]["source_uri"]
        == "gs://agentx-evidence/missions/test/tfsec.json"
    )
    assert claim_dto["evidence_items"][0]["collected_by_agent"] == "Auditor"

    # 3. Call GET /missions/{mission_id}/evidence/claims/{claim_id}
    detail_resp = client.get(
        f"/api/v1/missions/{mission_id}/evidence/claims/{claim.claim_id}",
        headers=headers,
    )
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["claim_id"] == claim.claim_id
    assert detail_data["final_decision_reason"].startswith("Certified as verified")
    assert len(detail_data["evidence_items"]) == 1

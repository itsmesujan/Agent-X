"""Unit and API Integration Tests for the Agent-X Artifact Center Subsystem."""

import hashlib

import pytest
from fastapi.testclient import TestClient

from agentx.api.schemas import ArtifactType
from agentx.api.state import state_manager
from agentx.main import app
from agentx.tools.impl.artifact_generation import ArtifactGenerationTool
from agentx.tools.schemas import ToolInvocationContext


@pytest.fixture(autouse=True)
def clean_state() -> None:
    """Reset the in-memory state manager before each test."""
    state_manager.missions.clear()
    state_manager.workflows.clear()
    state_manager.resource_brains.clear()
    state_manager.evidence_engines.clear()
    state_manager.recovery_engines.clear()
    state_manager.artifacts.clear()
    state_manager.approvals.clear()


def test_artifact_categorization_and_metadata_validation() -> None:
    """Verify all 5 required artifact categories with mission ID, created timestamp, and statuses."""
    client = TestClient(app)
    headers = {"Authorization": "Bearer dev-token-auditor"}

    mission = state_manager.create_mission(
        title="Artifact Categorization Verification",
        goal_statement="Deliver 5 categories of artifacts.",
    )
    mission_id = mission.mission_id

    # 1. Register artifacts for all 5 categories
    test_artifacts = [
        {
            "title": "System Architecture & Security Audit",
            "filename": "security_audit_report.md",
            "artifact_type": ArtifactType.REPORT.value,
            "content": "# Security Audit\nStatus: PASS\nAll IAM roles enforced.",
            "content_type": "text/markdown",
            "agent_role": "AUDITOR",
        },
        {
            "title": "Evaluation Benchmark Telemetry",
            "filename": "telemetry_dataset.json",
            "artifact_type": ArtifactType.DATASET.value,
            "content": '{"samples": 120, "mean_latency_ms": 42.5}',
            "content_type": "application/json",
            "agent_role": "TESTER",
        },
        {
            "title": "Executive Briefing Deck",
            "filename": "pitch_presentation.md",
            "artifact_type": ArtifactType.PRESENTATION.value,
            "content": "# Slide 1: Agent-X Mission Control\nAutonomous AI Engineering",
            "content_type": "text/markdown",
            "agent_role": "ARCHITECT",
        },
        {
            "title": "Mission Outcome Digest",
            "filename": "executive_summary.md",
            "artifact_type": ArtifactType.SUMMARY.value,
            "content": "All 12 DAG tasks completed with 100% verification fidelity.",
            "content_type": "text/markdown",
            "agent_role": "COORDINATOR",
        },
        {
            "title": "Signed Merkle Proof Manifest",
            "filename": "evidence_package_manifest.json",
            "artifact_type": ArtifactType.EVIDENCE_PACKAGE.value,
            "content": '{"merkle_root": "a8fbc329...", "proof_count": 8}',
            "content_type": "application/json",
            "agent_role": "AUDITOR",
        },
    ]

    for item in test_artifacts:
        resp = client.post(
            f"/api/v1/missions/{mission_id}/artifacts",
            json=item,
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["mission_id"] == mission_id
        assert data["title"] == item["title"]
        assert data["filename"] == item["filename"]
        assert data["artifact_type"] == item["artifact_type"]
        assert data["generation_status"] == "GENERATED"
        assert data["verification_status"] == "VERIFIED"
        assert len(data["sha256"]) == 64
        assert data["size_bytes"] == len(item["content"].encode("utf-8"))
        assert "created_at" in data

    # 2. Query all artifacts
    all_resp = client.get(f"/api/v1/missions/{mission_id}/artifacts", headers=headers)
    assert all_resp.status_code == 200
    all_data = all_resp.json()
    assert len(all_data) == 5

    # 3. Filter by category
    rep_resp = client.get(
        f"/api/v1/missions/{mission_id}/artifacts?category=REPORT", headers=headers
    )
    assert rep_resp.status_code == 200
    rep_data = rep_resp.json()
    assert len(rep_data) == 1
    assert rep_data[0]["filename"] == "security_audit_report.md"

    pkg_resp = client.get(
        f"/api/v1/missions/{mission_id}/artifacts?category=EVIDENCE_PACKAGE", headers=headers
    )
    assert pkg_resp.status_code == 200
    pkg_data = pkg_resp.json()
    assert len(pkg_data) == 1
    assert pkg_data[0]["filename"] == "evidence_package_manifest.json"


def test_artifact_detail_and_download_endpoints() -> None:
    """Verify single artifact inspection and file download headers & payloads."""
    client = TestClient(app)
    headers = {"Authorization": "Bearer dev-token-auditor"}

    mission = state_manager.create_mission(
        title="Download Action Verification",
        goal_statement="Test artifact file download stream.",
    )
    mission_id = mission.mission_id

    content_text = "# Executive Deliverable\nKey Metric: 99.9% uptime"
    create_resp = client.post(
        f"/api/v1/missions/{mission_id}/artifacts",
        json={
            "title": "Executive Summary",
            "filename": "summary.md",
            "artifact_type": "SUMMARY",
            "content": content_text,
            "content_type": "text/markdown",
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    art_data = create_resp.json()
    artifact_id = art_data["artifact_id"]

    # 1. Get Artifact Detail
    detail_resp = client.get(
        f"/api/v1/missions/{mission_id}/artifacts/{artifact_id}",
        headers=headers,
    )
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["artifact_id"] == artifact_id
    assert detail_data["content"] == content_text
    assert detail_data["sha256"] == hashlib.sha256(content_text.encode("utf-8")).hexdigest()

    # 2. Download Artifact
    dl_resp = client.get(
        f"/api/v1/missions/{mission_id}/artifacts/{artifact_id}/download",
        headers=headers,
    )
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-disposition"] == 'attachment; filename="summary.md"'
    assert dl_resp.text == content_text


@pytest.mark.asyncio
async def test_artifact_generation_tool_sha256_proof() -> None:
    """Verify ArtifactGenerationTool produces verified SHA-256 evidence."""
    tool = ArtifactGenerationTool()
    ctx = ToolInvocationContext(
        tool_name="artifact_generation",
        mission_id="msn_tool_test_01",
    )

    payload = {
        "filename": "dataset_export.csv",
        "content": "id,name,score\n1,Alpha,98\n2,Beta,95",
        "content_type": "text/csv",
    }
    ctx.parameters = payload

    result = await tool.execute(ctx)
    assert result.is_success is True
    assert result.data["filename"] == "dataset_export.csv"
    assert result.data["size_bytes"] == len(payload["content"].encode("utf-8"))
    assert result.data["sha256"] == hashlib.sha256(payload["content"].encode("utf-8")).hexdigest()

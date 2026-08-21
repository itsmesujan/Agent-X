"""Unit tests for Agent-X Verification Engine and 7-Dimension Certification Protocol."""

from agentx.evidence import EvidenceEngine, SourceReliability
from agentx.kernel.models import Goal, Mission, MissionState, SuccessCriteria
from agentx.verification import (
    VerificationDimension,
    VerificationEngine,
    VerificationOutcome,
)
from agentx_common.schemas import MissionBudget, MissionStatus, VerificationLevel


def make_test_mission(
    success_criteria: list[SuccessCriteria] | None = None,
    budget_usd: float = 10.0,
    deliverables: list[str] | None = None,
    constraints: dict[str, str] | None = None,
) -> Mission:
    goal = Goal(
        goal_statement="Deploy production multi-region Firestore backend",
        primary_objective="Deploy production Firestore",
        deliverables=deliverables or ["firestore_spec.json"],
        constraints=constraints or {"region": "us-central1"},
        success_criteria=success_criteria or [],
    )
    budget = MissionBudget(max_usd_limit=budget_usd)
    return Mission(
        mission_id="msn_vrf_01",
        title="Firestore Production Deployment",
        goal=goal,
        budget=budget,
        state=MissionState(status=MissionStatus.EXECUTING),
    )


def test_verification_pass_happy_path() -> None:
    """Test full PASS verification when all 7 dimensions are satisfied."""
    engine = VerificationEngine()
    ev_engine = EvidenceEngine()

    sc = [
        SuccessCriteria(
            description="P99 latency must be under 50ms",
            verification_level=VerificationLevel.LEVEL_4_SEMANTIC,
            expected_metric={
                "metric": "p99_latency_ms",
                "operator": "<=",
                "target": 50.0,
            },
        )
    ]
    mission = make_test_mission(
        success_criteria=sc,
        budget_usd=5.0,
        deliverables=["firestore_spec.json"],
    )

    # 1. Create and verify supporting claim
    claim = ev_engine.create_claim(
        mission_id=mission.mission_id,
        statement="Firestore is active in us-central1",
        subject="Firestore",
        predicate="status",
        value="ACTIVE",
        source_ref="gcloud firestore describe",
        source_reliability=SourceReliability.AUTHORITATIVE,
    )
    ev_engine.attach_evidence(
        claim_id=claim.claim_id,
        content='{"status": "ACTIVE"}',
        source_uri="gs://agentx-evidence/firestore.json",
    )
    ev_engine.verify_claim(claim.claim_id)

    # 2. Valid deliverables with valid 64-char SHA256
    valid_sha = "a" * 64
    deliverables = [
        {
            "filename": "firestore_spec.json",
            "sha256": valid_sha,
            "size_bytes": 1024,
            "p99_latency_ms": 32.5,  # Satisfies <= 50.0
        }
    ]

    context = {
        "consumed_budget_usd": 1.25,
        "constraint_region": True,
        "expected_artifacts": ["firestore_spec.json"],
    }

    report = engine.verify_mission(
        mission=mission,
        evidence_engine=ev_engine,
        deliverables=deliverables,
        context_data=context,
    )

    assert report.overall_outcome == VerificationOutcome.PASS
    assert report.overall_score >= 0.90
    assert len(report.failed_checks) == 0
    assert len(report.evaluator_signature) == 64  # HMAC-SHA256


def test_verification_repair_required_on_missing_artifact() -> None:
    """Test REPAIR_REQUIRED outcome when an expected artifact is missing."""
    engine = VerificationEngine()
    mission = make_test_mission(deliverables=["architecture.md", "terraform.tf"])

    valid_sha = "b" * 64
    deliverables = [
        {
            "filename": "architecture.md",
            "sha256": valid_sha,
            "size_bytes": 500,
        }
    ]

    # Context expects both architecture.md and terraform.tf
    context = {
        "consumed_budget_usd": 0.50,
        "expected_artifacts": ["architecture.md", "terraform.tf"],
    }

    report = engine.verify_mission(
        mission=mission,
        deliverables=deliverables,
        context_data=context,
    )

    assert report.overall_outcome == VerificationOutcome.REPAIR_REQUIRED
    assert len(report.failed_checks) > 0
    assert any("terraform.tf" in c.details for c in report.failed_checks)
    assert len(report.repair_recommendations) > 0
    assert any("terraform.tf" in r for r in report.repair_recommendations)


def test_verification_fail_on_critical_security_breach() -> None:
    """Test FAIL outcome immediately triggered upon fatal security risk condition."""
    engine = VerificationEngine()
    mission = make_test_mission()

    valid_sha = "c" * 64
    deliverables = [
        {
            "filename": "firestore_spec.json",
            "sha256": valid_sha,
            "size_bytes": 200,
        }
    ]

    context = {
        "consumed_budget_usd": 0.10,
        "security_breach_detected": True,  # Fatal risk violation
    }

    report = engine.verify_mission(
        mission=mission,
        deliverables=deliverables,
        context_data=context,
    )

    assert report.overall_outcome == VerificationOutcome.FAIL
    assert any("Fatal security" in r for r in report.repair_recommendations)


def test_anti_hallucination_zero_deliverables_refusal() -> None:
    """Test that an LLM generating text without concrete deliverables is rejected."""
    engine = VerificationEngine()
    mission = make_test_mission()

    # Empty deliverables list
    report = engine.verify_mission(
        mission=mission,
        deliverables=[],
        context_data={"consumed_budget_usd": 0.05},
    )

    assert report.overall_outcome in (VerificationOutcome.FAIL, VerificationOutcome.REPAIR_REQUIRED)
    ev_eval = report.dimension_evaluations[VerificationDimension.EVIDENCE.value]
    assert ev_eval.passed is False
    assert "No deliverables" in ev_eval.checks[0].details

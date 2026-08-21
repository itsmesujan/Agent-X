"""Unit tests for Agent-X World Model and Epistemic State Engine."""

from agentx.goal_engine.schemas import RiskLevel
from agentx.world_model import (
    Claim,
    Constraint,
    EntityType,
    Fact,
    Observation,
    RelationshipType,
    Risk,
    SourceProvenance,
    SourceType,
    Unknown,
    WorldModel,
    WorldModelEntity,
)
from agentx_common.schemas import AgentRole, EpistemicState


def create_world_model() -> WorldModel:
    return WorldModel(mission_id="msn_wm_01")


def test_entity_registration_and_update() -> None:
    wm = create_world_model()

    entity = WorldModelEntity(
        entity_id="service:cloud-run-api",
        mission_id="msn_wm_01",
        entity_type=EntityType.CLOUD_SERVICE,
        name="agentx-api",
        properties={"port": 8000, "region": "us-central1"},
        epistemic_state=EpistemicState.INFERRED_ASSUMPTION,
        confidence=0.8,
    )

    wm.register_entity(entity)
    fetched = wm.get_entity("service:cloud-run-api")

    assert fetched is not None
    assert fetched.name == "agentx-api"
    assert fetched.epistemic_state == EpistemicState.INFERRED_ASSUMPTION

    # Update entity properties and elevate to KNOWN_FACT
    updated = wm.update_entity_properties(
        entity_id="service:cloud-run-api",
        properties={"ingress": "all", "memory": "1Gi"},
        confidence=1.0,
        epistemic_state=EpistemicState.KNOWN_FACT,
        evidence_uri="gs://agentx-evidence/msn_wm_01/gcloud_describe.json",
    )

    assert updated.properties["ingress"] == "all"
    assert updated.confidence == 1.0
    assert updated.epistemic_state == EpistemicState.KNOWN_FACT
    assert updated.evidence_uri == "gs://agentx-evidence/msn_wm_01/gcloud_describe.json"


def test_fact_assertion_and_observation_linking() -> None:
    wm = create_world_model()

    # 1. Record empirical tool observation
    obs = Observation(
        observation_id="obs_gcloud_01",
        mission_id="msn_wm_01",
        source=SourceProvenance(
            source_type=SourceType.TOOL_EXECUTION,
            source_ref="gcloud run services describe agentx-api",
            task_id="task_audit_01",
            agent_role=AgentRole.DEVOPS,
            evidence_uri="gs://agentx-evidence/msn_wm_01/gcloud.log",
            raw_evidence_hash="a1b2c3d4e5f67890",
        ),
        raw_data={"status": {"url": "https://api.agentx.dev"}},
        summary="Retrieved live Cloud Run URL",
    )
    wm.record_observation(obs)

    # 2. Assert derived Fact
    fact = Fact(
        fact_id="fct_url_01",
        mission_id="msn_wm_01",
        entity_id="service:cloud-run-api",
        subject="Cloud Run agentx-api",
        predicate="public_url",
        value="https://api.agentx.dev",
        epistemic_state=EpistemicState.KNOWN_FACT,
        confidence=1.0,
        source=obs.source,
        observation_ids=["obs_gcloud_01"],
    )
    wm.assert_fact(fact)

    active_facts = wm.get_active_facts(subject="Cloud Run")
    assert len(active_facts) == 1
    assert active_facts[0].value == "https://api.agentx.dev"


def test_fact_invalidation() -> None:
    wm = create_world_model()

    fact = Fact(
        fact_id="fct_port_01",
        mission_id="msn_wm_01",
        subject="Backend Port",
        predicate="port",
        value=3000,
        source=SourceProvenance(
            source_type=SourceType.LLM_INFERENCE,
            source_ref="Assumption from package.json",
        ),
    )
    wm.assert_fact(fact)
    assert len(wm.get_active_facts()) == 1

    # Invalidate when empirical evidence shows port 8000
    invalidated = wm.invalidate_fact(
        fact_id="fct_port_01",
        reason="Port 3000 refuted by Dockerfile EXPOSE 8000 directive",
    )

    assert not invalidated.is_valid
    assert invalidated.invalidated_reason is not None
    assert "refuted by Dockerfile" in invalidated.invalidated_reason
    assert len(wm.get_active_facts()) == 0


def test_fact_superseding() -> None:
    wm = create_world_model()

    old_fact = Fact(
        fact_id="fct_version_v1",
        mission_id="msn_wm_01",
        subject="agent-x-core",
        predicate="version",
        value="0.1.0",
        source=SourceProvenance(source_type=SourceType.FILE_CONTENT, source_ref="package.json"),
    )
    wm.assert_fact(old_fact)

    new_fact = Fact(
        fact_id="fct_version_v2",
        mission_id="msn_wm_01",
        subject="agent-x-core",
        predicate="version",
        value="0.2.0",
        source=SourceProvenance(
            source_type=SourceType.TOOL_EXECUTION, source_ref="npm version minor"
        ),
    )

    old_f, new_f, edge = wm.supersede_fact(
        old_fact_id="fct_version_v1",
        new_fact=new_fact,
        reason="Bumped to minor version 0.2.0",
    )

    assert not old_f.is_valid
    assert old_f.superseded_by_fact_id == "fct_version_v2"
    assert new_f.is_valid
    assert edge.relationship == RelationshipType.SUPERSEDES
    assert edge.source_id == "fct_version_v2"
    assert edge.target_id == "fct_version_v1"


def test_unknown_resolution() -> None:
    wm = create_world_model()

    unknown = Unknown(
        unknown_id="unk_iam_roles",
        mission_id="msn_wm_01",
        question="Does the Cloud Run service account have Secret Manager Secret Accessor role?",
        impact="Blocks deployment of agentx-api service",
        blocking_task_ids=["task_deploy_01"],
    )
    wm.register_unknown(unknown)
    assert len(wm.get_unresolved_unknowns()) == 1

    # Assert fact resolving the unknown
    fact = Fact(
        fact_id="fct_iam_resolved",
        mission_id="msn_wm_01",
        subject="Service Account IAM",
        predicate="roles/secretmanager.secretAccessor",
        value=True,
        source=SourceProvenance(
            source_type=SourceType.TOOL_EXECUTION,
            source_ref="gcloud projects get-iam-policy",
        ),
    )
    wm.assert_fact(fact)

    # Resolve unknown
    resolved = wm.resolve_unknown(
        unknown_id="unk_iam_roles",
        resolved_fact_id="fct_iam_resolved",
    )

    assert resolved.is_resolved
    assert resolved.resolved_fact_id == "fct_iam_resolved"
    assert len(wm.get_unresolved_unknowns()) == 0


def test_provenance_trace() -> None:
    """Verify end-to-end provenance traversal from Fact back to raw Evidence URI and hashes."""
    wm = create_world_model()

    obs = Observation(
        observation_id="obs_test_exit_01",
        mission_id="msn_wm_01",
        source=SourceProvenance(
            source_type=SourceType.TOOL_EXECUTION,
            source_ref="pytest tests/unit",
            task_id="task_run_tests",
            agent_role=AgentRole.TESTER,
            evidence_uri="gs://agentx-evidence/msn_wm_01/pytest_output.xml",
            raw_evidence_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        ),
        raw_data={"passed": 48, "failed": 0},
        summary="All 48 unit tests passed",
    )
    wm.record_observation(obs)

    fact = Fact(
        fact_id="fct_tests_green",
        mission_id="msn_wm_01",
        entity_id="test_suite:unit",
        subject="Unit Test Suite",
        predicate="all_passing",
        value=True,
        source=obs.source,
        observation_ids=["obs_test_exit_01"],
    )
    wm.assert_fact(fact)

    trace = wm.trace_provenance("fct_tests_green")

    assert trace.target_id == "fct_tests_green"
    assert trace.target_type == "FACT"
    assert len(trace.facts) == 1
    assert len(trace.observations) == 1
    assert "gs://agentx-evidence/msn_wm_01/pytest_output.xml" in trace.evidence_uris
    assert (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" in trace.evidence_hashes
    )
    assert len(trace.chain_of_custody) >= 2


def test_environment_snapshot() -> None:
    wm = create_world_model()

    wm.register_constraint(
        Constraint(
            mission_id="msn_wm_01",
            name="No Destructive IAM",
            rule_statement="Do not delete existing IAM bindings",
        )
    )
    wm.register_risk(
        Risk(
            mission_id="msn_wm_01",
            title="Public Ingress Risk",
            description="Exposing service without authentication header",
            severity=RiskLevel.HIGH,
        )
    )
    wm.make_claim(
        Claim(
            mission_id="msn_wm_01",
            statement="Cloud Run cold starts may exceed 2 seconds",
            agent_role=AgentRole.ARCHITECT,
        )
    )

    snapshot = wm.get_environment_snapshot()

    assert snapshot["mission_id"] == "msn_wm_01"
    assert snapshot["constraints_count"] == 1
    assert snapshot["active_risks_count"] == 1

"""Integration tests for World Model semantic graph persistence and complex multi-hop provenance tracing."""

from agentx.goal_engine.schemas import RiskLevel
from agentx.world_model import (
    Constraint,
    EntityType,
    Fact,
    InMemoryWorldModelStore,
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


def test_full_mission_semantic_graph_lifecycle() -> None:
    """Integration test building a complete, complex World Model graph and executing multi-hop tracing."""
    store = InMemoryWorldModelStore()
    wm = WorldModel(mission_id="msn_integration_01", store=store)

    # 1. Register base environmental entities
    repo_entity = WorldModelEntity(
        entity_id="repo:agent-x",
        mission_id="msn_integration_01",
        entity_type=EntityType.REPOSITORY,
        name="agent-x-monorepo",
        properties={"branch": "main", "language": "python/typescript"},
    )
    wm.register_entity(repo_entity)

    service_entity = WorldModelEntity(
        entity_id="cloud_run:agentx-api",
        mission_id="msn_integration_01",
        entity_type=EntityType.CLOUD_SERVICE,
        name="agentx-api",
        properties={"region": "us-central1", "service_account": "agentx-sa@gcp.iam"},
    )
    wm.register_entity(service_entity)

    secret_entity = WorldModelEntity(
        entity_id="secret:GEMINI_API_KEY",
        mission_id="msn_integration_01",
        entity_type=EntityType.SECRET_POINTER,
        name="GEMINI_API_KEY",
        properties={"secret_manager_path": "projects/my-proj/secrets/GEMINI_API_KEY"},
    )
    wm.register_entity(secret_entity)

    # 2. Establish semantic directed edges between entities
    wm.link_nodes("repo:agent-x", "cloud_run:agentx-api", RelationshipType.MUTATES)
    wm.link_nodes(
        "cloud_run:agentx-api", "secret:GEMINI_API_KEY", RelationshipType.AUTHENTICATES_VIA
    )

    # 3. Add Constraints and Risks
    wm.register_constraint(
        Constraint(
            mission_id="msn_integration_01",
            name="Max Spend Cap",
            rule_statement="USD total cost cannot exceed $5.00",
        )
    )
    wm.register_risk(
        Risk(
            mission_id="msn_integration_01",
            title="Secret Leaks in Git",
            description="Prevent committing plain-text credentials",
            severity=RiskLevel.CRITICAL,
        )
    )

    # 4. Create an unknown blocking deployment
    unknown = Unknown(
        unknown_id="unk_sa_secret_access",
        mission_id="msn_integration_01",
        question="Can agentx-sa@gcp.iam read secret GEMINI_API_KEY?",
        impact="Blocks Cloud Run cold start",
    )
    wm.register_unknown(unknown)
    wm.link_nodes(
        "cloud_run:agentx-api", "unk_sa_secret_access", RelationshipType.BLOCKED_BY_UNKNOWN
    )

    # 5. Execute exploratory task and capture observation
    obs = Observation(
        observation_id="obs_iam_binding_check",
        mission_id="msn_integration_01",
        source=SourceProvenance(
            source_type=SourceType.TOOL_EXECUTION,
            source_ref="gcloud secrets get-iam-policy GEMINI_API_KEY",
            task_id="task_verify_iam_01",
            agent_role=AgentRole.DEVOPS,
            evidence_uri="gs://agentx-evidence/msn_integration_01/secret_iam.json",
            raw_evidence_hash="fedcba9876543210",
        ),
        raw_data={
            "bindings": [
                {
                    "role": "roles/secretmanager.secretAccessor",
                    "members": ["serviceAccount:agentx-sa@gcp.iam"],
                }
            ]
        },
        summary="Service Account verified to hold Secret Accessor role",
    )
    wm.record_observation(obs)

    # 6. Assert verified Fact and resolve unknown
    fact = Fact(
        fact_id="fct_secret_access_verified",
        mission_id="msn_integration_01",
        entity_id="cloud_run:agentx-api",
        subject="Cloud Run Secret Access",
        predicate="has_secret_accessor_role",
        value=True,
        epistemic_state=EpistemicState.KNOWN_FACT,
        confidence=1.0,
        source=obs.source,
        observation_ids=["obs_iam_binding_check"],
    )
    wm.assert_fact(fact)
    wm.resolve_unknown("unk_sa_secret_access", "fct_secret_access_verified")

    # 7. Query verification
    assert len(wm.get_unresolved_unknowns()) == 0
    active_facts = wm.get_active_facts(entity_id="cloud_run:agentx-api")
    assert len(active_facts) == 1
    assert active_facts[0].value is True

    # 8. Multi-hop Provenance Tracing from Fact back to Evidence
    trace = wm.trace_provenance("fct_secret_access_verified")
    assert trace.target_id == "fct_secret_access_verified"
    assert "gs://agentx-evidence/msn_integration_01/secret_iam.json" in trace.evidence_uris
    assert "fedcba9876543210" in trace.evidence_hashes
    assert len(trace.observations) == 1
    assert len(trace.chain_of_custody) >= 2

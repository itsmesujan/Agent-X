"""Unit tests for Google Cloud Firestore Native Mode Persistence Store."""

import pytest

from agentx.evidence.schemas import EvidenceClaim, EvidenceItem, SourceReliability
from agentx.gcp.firestore import FirestoreClientFactory, GoogleCloudFirestoreStore
from agentx.kernel.events import EventType, KernelEvent
from agentx.kernel.models import Goal, Mission, MissionState, Task
from agentx_common.schemas import AgentRole, MissionBudget, MissionStatus


@pytest.fixture
def firestore_store() -> GoogleCloudFirestoreStore:
    client = FirestoreClientFactory.create_client(use_mock=True)
    return GoogleCloudFirestoreStore(client=client)


def test_firestore_missions_crud(firestore_store: GoogleCloudFirestoreStore) -> None:
    """Test Firestore /missions/{id} collection CRUD."""
    mission = Mission(
        mission_id="msn_gcp_001",
        title="Migrate DB to Cloud SQL",
        goal=Goal(
            goal_statement="Deploy multi-region DB",
            primary_objective="Deploy DB",
            deliverables=["schema.sql"],
        ),
        budget=MissionBudget(max_usd_limit=25.0),
        state=MissionState(status=MissionStatus.READY),
    )

    # 1. Save
    firestore_store.save_mission(mission)

    # 2. Get
    fetched = firestore_store.get_mission("msn_gcp_001")
    assert fetched is not None
    assert fetched.mission_id == "msn_gcp_001"
    assert fetched.budget.max_usd_limit == 25.0

    # 3. List
    missions = firestore_store.list_missions()
    assert len(missions) == 1
    assert missions[0].mission_id == "msn_gcp_001"

    # 4. Delete
    firestore_store.delete_mission("msn_gcp_001")
    assert firestore_store.get_mission("msn_gcp_001") is None


def test_firestore_tasks_and_atomic_locks(firestore_store: GoogleCloudFirestoreStore) -> None:
    """Test Firestore /missions/{id}/tasks/{taskId} subcollection and lease locks."""
    task = Task(
        task_id="task_audit_iam",
        mission_id="msn_gcp_002",
        name="Audit IAM Roles",
        description="Check permissions",
        agent_role=AgentRole.AUDITOR,
    )

    # 1. Save and Get
    firestore_store.save_task(task)
    fetched_task = firestore_store.get_task("msn_gcp_002", "task_audit_iam")
    assert fetched_task is not None
    assert fetched_task.name == "Audit IAM Roles"

    # 2. Acquire lock with worker 1
    lock_ok = firestore_store.acquire_task_lock(
        "msn_gcp_002", "task_audit_iam", "worker_alpha", lease_seconds=300
    )
    assert lock_ok is True

    # 3. Worker 2 attempts concurrent lock acquisition -> fails
    lock_fail = firestore_store.acquire_task_lock(
        "msn_gcp_002", "task_audit_iam", "worker_beta", lease_seconds=300
    )
    assert lock_fail is False

    # 4. Release lock with worker 1
    release_ok = firestore_store.release_task_lock("msn_gcp_002", "task_audit_iam", "worker_alpha")
    assert release_ok is True

    # 5. Worker 2 can now acquire lock
    lock_ok2 = firestore_store.acquire_task_lock(
        "msn_gcp_002", "task_audit_iam", "worker_beta", lease_seconds=300
    )
    assert lock_ok2 is True


def test_firestore_workflows_events_agents(firestore_store: GoogleCloudFirestoreStore) -> None:
    """Test workflows, events, and agent states persistence."""
    mission_id = "msn_gcp_003"

    # 1. Workflows
    wf_data = {"workflow_id": "wf_001", "task_count": 5, "root_tasks": ["t1"]}
    firestore_store.save_workflow(mission_id, "wf_001", wf_data)
    assert firestore_store.get_workflow(mission_id, "wf_001") == wf_data

    # 2. Events
    event = KernelEvent(
        mission_id=mission_id,
        event_type=EventType.MISSION_STATE_CHANGED,
        payload={"started_by": "operator"},
    )
    firestore_store.record_event(event)
    events = firestore_store.get_events(mission_id)
    assert len(events) == 1
    assert events[0].event_id == event.event_id

    # 3. Agents
    agent_state = {"agent_id": "agent_planner", "status": "IDLE", "tasks_executed": 4}
    firestore_store.save_agent_state(mission_id, "agent_planner", agent_state)
    assert firestore_store.get_agent_state(mission_id, "agent_planner") == agent_state
    assert len(firestore_store.list_agent_states(mission_id)) == 1


def test_firestore_claims_evidence_resources_approvals_artifacts(
    firestore_store: GoogleCloudFirestoreStore,
) -> None:
    """Test claims, evidence, resources, approvals, and artifacts persistence."""
    mission_id = "msn_gcp_004"

    # 1. Claims
    claim = EvidenceClaim(
        claim_id="clm_001",
        mission_id=mission_id,
        statement="Database is SSL encrypted",
        subject="Database",
        predicate="ssl_enabled",
        value=True,
        source_ref="gcloud_describe",
        source_reliability=SourceReliability.PRIMARY_EVIDENCE,
    )
    firestore_store.save_claim(claim)
    assert firestore_store.get_claim(mission_id, "clm_001") is not None
    assert len(firestore_store.list_claims(mission_id)) == 1

    # 2. Evidence
    evidence = EvidenceItem(
        evidence_id="evd_001",
        source_uri="gcloud sql instances describe",
        content_ref="ssl_config",
        raw_data_hash="e" * 64,
        byte_size=1024,
    )
    firestore_store.save_evidence(mission_id, evidence)
    assert firestore_store.get_evidence(mission_id, "evd_001") is not None
    assert len(firestore_store.list_evidence(mission_id)) == 1

    # 3. Resources
    snapshot = {"usd_spent": 1.25, "tokens_used": 15000, "active_locks": {}}
    firestore_store.save_resource_snapshot(mission_id, snapshot)
    assert firestore_store.get_resource_snapshot(mission_id) == snapshot

    # 4. Approvals
    approval_data = {"approval_id": "app_001", "status": "PENDING", "task_id": "t1"}
    firestore_store.save_approval("app_001", approval_data)
    assert firestore_store.get_approval("app_001") == approval_data
    assert len(firestore_store.list_approvals(status="PENDING")) == 1

    # 5. Artifacts
    artifact_data = {"artifact_id": "art_001", "filename": "schema.sql", "sha256": "a" * 64}
    firestore_store.save_artifact(mission_id, "art_001", artifact_data)
    assert firestore_store.get_artifact(mission_id, "art_001") == artifact_data
    assert len(firestore_store.list_artifacts(mission_id)) == 1

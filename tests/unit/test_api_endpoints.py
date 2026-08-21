"""Comprehensive API Integration and Route Tests for Agent-X FastAPI Backend."""

from fastapi.testclient import TestClient

from agentx.api.state import state_manager
from agentx.main import app
from agentx_common.schemas import AgentRole, MissionStatus

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer dev-token-commander"}


def test_openapi_schema_endpoint() -> None:
    """Verify OpenAPI 3.1 specification schema is correctly exposed."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Agent-X Mission Control API"
    assert "/api/v1/missions" in schema["paths"]
    assert "/api/v1/approvals/{approval_id}/approve" in schema["paths"]


def test_auth_rejection_on_missing_header() -> None:
    """Verify endpoints reject requests without a valid Authorization header with 401."""
    response = client.get("/api/v1/missions")
    assert response.status_code == 401
    assert "Missing Authorization header" in response.json()["error"]["message"]


def test_create_and_list_missions() -> None:
    """Test POST /missions and GET /missions endpoints."""
    payload = {
        "title": "Deploy Cloud SQL Database",
        "goal_statement": "Deploy high availability Cloud SQL PostgreSQL instance",
        "max_usd_budget": 10.00,
        "max_runtime_minutes": 45,
        "deliverables": ["terraform.tf", "schema.sql"],
        "constraints": {"region": "us-central1"},
    }

    # 1. Create Mission
    post_res = client.post("/api/v1/missions", json=payload, headers=AUTH_HEADERS)
    assert post_res.status_code == 201
    created = post_res.json()
    mission_id = created["mission_id"]
    assert created["title"] == payload["title"]
    assert created["status"] == MissionStatus.READY.value

    # 2. List Missions
    list_res = client.get("/api/v1/missions", headers=AUTH_HEADERS)
    assert list_res.status_code == 200
    missions = list_res.json()
    assert len(missions) >= 1
    assert any(m["mission_id"] == mission_id for m in missions)


def test_mission_lifecycle_control_endpoints() -> None:
    """Test GET /missions/{id}, POST /start, /pause, /resume, /cancel."""
    # Create test mission
    post_res = client.post(
        "/api/v1/missions",
        json={
            "title": "Lifecycle Mission",
            "goal_statement": "Test state transitions via API",
            "max_usd_budget": 5.0,
            "max_runtime_minutes": 30,
        },
        headers=AUTH_HEADERS,
    )
    mission_id = post_res.json()["mission_id"]

    # 1. Get Detail
    detail_res = client.get(f"/api/v1/missions/{mission_id}", headers=AUTH_HEADERS)
    assert detail_res.status_code == 200
    assert detail_res.json()["mission_id"] == mission_id

    # 2. Start
    start_res = client.post(f"/api/v1/missions/{mission_id}/start", headers=AUTH_HEADERS)
    assert start_res.status_code == 200
    assert start_res.json()["status"] == MissionStatus.EXECUTING.value

    # 3. Pause
    pause_res = client.post(f"/api/v1/missions/{mission_id}/pause", headers=AUTH_HEADERS)
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == MissionStatus.PAUSED.value

    # 4. Resume
    resume_res = client.post(f"/api/v1/missions/{mission_id}/resume", headers=AUTH_HEADERS)
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == MissionStatus.EXECUTING.value

    # 5. Cancel
    cancel_res = client.post(f"/api/v1/missions/{mission_id}/cancel", headers=AUTH_HEADERS)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == MissionStatus.ABORTED.value


def test_mission_tasks_and_graph_endpoints() -> None:
    """Test GET /missions/{id}/tasks and GET /missions/{id}/graph."""
    post_res = client.post(
        "/api/v1/missions",
        json={
            "title": "DAG Graph Mission",
            "goal_statement": "Test DAG visualization",
            "max_usd_budget": 5.0,
            "max_runtime_minutes": 30,
        },
        headers=AUTH_HEADERS,
    )
    mission_id = post_res.json()["mission_id"]
    wf = state_manager.get_workflow(mission_id)
    assert wf is not None

    # Populate tasks in workflow
    wf.create_task(
        task_id="t1", name="Audit Code", description="Desc", agent_role=AgentRole.ARCHITECT
    )
    wf.create_task(
        task_id="t2",
        name="Generate Patch",
        description="Desc",
        agent_role=AgentRole.CODER,
        dependencies=["t1"],
    )

    # 1. GET /tasks
    tasks_res = client.get(f"/api/v1/missions/{mission_id}/tasks", headers=AUTH_HEADERS)
    assert tasks_res.status_code == 200
    tasks_data = tasks_res.json()
    assert len(tasks_data) == 2
    assert tasks_data[0]["task_id"] == "t1"
    assert tasks_data[1]["dependencies"] == ["t1"]

    # 2. GET /graph
    graph_res = client.get(f"/api/v1/missions/{mission_id}/graph", headers=AUTH_HEADERS)
    assert graph_res.status_code == 200
    graph_data = graph_res.json()
    assert len(graph_data["nodes"]) == 2
    assert len(graph_data["edges"]) == 1
    assert graph_data["edges"][0]["source"] == "t1"
    assert graph_data["edges"][0]["target"] == "t2"


def test_mission_events_resources_evidence_artifacts() -> None:
    """Test GET /events, /resources, /evidence, /artifacts endpoints."""
    post_res = client.post(
        "/api/v1/missions",
        json={
            "title": "Telemetry Mission",
            "goal_statement": "Test telemetry and evidence inspection",
            "max_usd_budget": 15.0,
            "max_runtime_minutes": 60,
        },
        headers=AUTH_HEADERS,
    )
    mission_id = post_res.json()["mission_id"]

    # Populate evidence and artifacts in state
    ee = state_manager.get_evidence_engine(mission_id)
    assert ee is not None
    ee.create_claim(
        mission_id=mission_id,
        statement="Database is replicated",
        subject="Database",
        predicate="replication",
        value=True,
        source_ref="gcloud",
    )

    state_manager.artifacts[mission_id].append(
        {
            "filename": "database.tf",
            "sha256": "f" * 64,
            "size_bytes": 2048,
            "gcs_uri": f"gs://agentx-evidence/missions/{mission_id}/database.tf",
            "task_id": "t1",
        }
    )

    # 1. GET /events
    events_res = client.get(f"/api/v1/missions/{mission_id}/events", headers=AUTH_HEADERS)
    assert events_res.status_code == 200
    assert isinstance(events_res.json(), list)

    # 2. GET /resources
    res_res = client.get(f"/api/v1/missions/{mission_id}/resources", headers=AUTH_HEADERS)
    assert res_res.status_code == 200
    res_data = res_res.json()
    assert res_data["max_usd_limit"] == 15.0

    # 3. GET /evidence
    evd_res = client.get(f"/api/v1/missions/{mission_id}/evidence", headers=AUTH_HEADERS)
    assert evd_res.status_code == 200
    evd_data = evd_res.json()
    assert evd_data["total_claims"] == 1

    # 4. GET /artifacts
    art_res = client.get(f"/api/v1/missions/{mission_id}/artifacts", headers=AUTH_HEADERS)
    assert art_res.status_code == 200
    art_data = art_res.json()
    assert len(art_data) == 1
    assert art_data[0]["filename"] == "database.tf"


def test_hitl_approval_and_rejection_endpoints() -> None:
    """Test POST /approvals/{id}/approve and POST /approvals/{id}/reject."""
    # Create mission and register pending approval
    mission = state_manager.create_mission(
        title="HITL Approval Test Mission",
        goal_statement="Perform secure cloud rollout",
    )
    mission.state.status = MissionStatus.PAUSED

    approval = state_manager.register_approval(
        mission_id=mission.mission_id,
        task_id="task_cloud_apply",
        reason="Terraform apply requires operator sign-off",
    )

    # 1. Test 404 on invalid approval ID
    bad_res = client.post("/api/v1/approvals/bad_id/approve", json={}, headers=AUTH_HEADERS)
    assert bad_res.status_code == 404

    # 2. Approve
    app_res = client.post(
        f"/api/v1/approvals/{approval.approval_id}/approve",
        json={"decision_notes": "Reviewed terraform plan; approved."},
        headers=AUTH_HEADERS,
    )
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "APPROVED"
    assert mission.state.status == MissionStatus.EXECUTING

    # 3. Register second approval to test Reject
    approval2 = state_manager.register_approval(
        mission_id=mission.mission_id,
        task_id="task_delete_vm",
        reason="Delete compute instance requires sign-off",
    )
    rej_res = client.post(
        f"/api/v1/approvals/{approval2.approval_id}/reject",
        json={"decision_notes": "Do not delete instance yet."},
        headers=AUTH_HEADERS,
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "REJECTED"

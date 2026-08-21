"""Google Cloud Firestore Persistence Store for Agent-X Native Mode Entities."""

from datetime import UTC, datetime
from typing import Any

from agentx.evidence.schemas import EvidenceClaim, EvidenceItem
from agentx.gcp.firestore.client import MockFirestoreClient
from agentx.kernel.events import KernelEvent
from agentx.kernel.models import Mission, Task
from agentx.kernel.persistence import EntityNotFoundError, StateStore


class GoogleCloudFirestoreStore(StateStore):
    """Production and Emulator Firestore implementation covering all 10 Agent-X entities.

    Entities:
    1. missions       -> /missions/{missionId}
    2. tasks          -> /missions/{missionId}/tasks/{taskId}
    3. workflows      -> /missions/{missionId}/workflows/{workflowId}
    4. events         -> /missions/{missionId}/events/{eventId}
    5. agents         -> /missions/{missionId}/agents/{agentId}
    6. claims         -> /missions/{missionId}/claims/{claimId}
    7. evidence       -> /missions/{missionId}/evidence/{evidenceId}
    8. resources      -> /missions/{missionId}/resources/{resourceId}
    9. approvals      -> /approvals/{approvalId}
    10. artifacts     -> /missions/{missionId}/artifacts/{artifactId}
    """

    def __init__(self, client: MockFirestoreClient | Any) -> None:
        self.client = client

    # --- 1. MISSIONS ---

    def save_mission(self, mission: Mission) -> None:
        doc_ref = self.client.collection("missions").document(mission.mission_id)
        doc_ref.set(mission.model_dump(mode="json"))

    def get_mission(self, mission_id: str) -> Mission | None:
        doc_ref = self.client.collection("missions").document(mission_id)
        snap = doc_ref.get()
        if not snap.exists or not snap.to_dict():
            return None
        return Mission.model_validate(snap.to_dict())

    def list_missions(self) -> list[Mission]:
        snaps = self.client.collection("missions").stream()
        return [Mission.model_validate(s.to_dict()) for s in snaps if s.to_dict()]

    def delete_mission(self, mission_id: str) -> None:
        self.client.collection("missions").document(mission_id).delete()

    # --- 2. TASKS ---

    def save_task(self, task: Task) -> None:
        doc_ref = (
            self.client.collection("missions")
            .document(task.mission_id)
            .collection("tasks")
            .document(task.task_id)
        )
        doc_ref.set(task.model_dump(mode="json"))

    def get_task(self, mission_id: str, task_id: str) -> Task | None:
        doc_ref = (
            self.client.collection("missions")
            .document(mission_id)
            .collection("tasks")
            .document(task_id)
        )
        snap = doc_ref.get()
        if not snap.exists or not snap.to_dict():
            return None
        return Task.model_validate(snap.to_dict())

    def list_tasks(self, mission_id: str) -> list[Task]:
        snaps = self.client.collection("missions").document(mission_id).collection("tasks").stream()
        return [Task.model_validate(s.to_dict()) for s in snaps if s.to_dict()]

    def acquire_task_lock(
        self,
        mission_id: str,
        task_id: str,
        worker_id: str,
        lease_seconds: int = 300,
    ) -> bool:
        doc_ref = (
            self.client.collection("missions")
            .document(mission_id)
            .collection("tasks")
            .document(task_id)
        )
        snap = doc_ref.get()
        if not snap.exists or not snap.to_dict():
            raise EntityNotFoundError(f"Task '{task_id}' in mission '{mission_id}' not found")

        data = snap.to_dict() or {}
        current_lock = data.get("locked_by_worker_id")
        lock_expires_at = data.get("lock_expires_at")
        now_ts = datetime.now(UTC).timestamp()

        if current_lock and current_lock != worker_id and lock_expires_at:
            if isinstance(lock_expires_at, (int, float)) and lock_expires_at > now_ts:
                return False

        new_expires = now_ts + lease_seconds
        doc_ref.update(
            {
                "locked_by_worker_id": worker_id,
                "lock_expires_at": new_expires,
            }
        )
        return True

    def release_task_lock(self, mission_id: str, task_id: str, worker_id: str) -> bool:
        doc_ref = (
            self.client.collection("missions")
            .document(mission_id)
            .collection("tasks")
            .document(task_id)
        )
        snap = doc_ref.get()
        if not snap.exists or not snap.to_dict():
            return True

        data = snap.to_dict() or {}
        if data.get("locked_by_worker_id") == worker_id:
            doc_ref.update(
                {
                    "locked_by_worker_id": None,
                    "lock_expires_at": None,
                }
            )
            return True
        return False

    # --- 3. WORKFLOWS ---

    def save_workflow(
        self, mission_id: str, workflow_id: str, workflow_data: dict[str, Any]
    ) -> None:
        doc_ref = (
            self.client.collection("missions")
            .document(mission_id)
            .collection("workflows")
            .document(workflow_id)
        )
        doc_ref.set(workflow_data)

    def get_workflow(self, mission_id: str, workflow_id: str) -> dict[str, Any] | None:
        doc_ref = (
            self.client.collection("missions")
            .document(mission_id)
            .collection("workflows")
            .document(workflow_id)
        )
        snap = doc_ref.get()
        return snap.to_dict() if snap.exists else None

    # --- 4. EVENTS ---

    def record_event(self, event: KernelEvent) -> None:
        doc_ref = (
            self.client.collection("missions")
            .document(event.mission_id)
            .collection("events")
            .document(event.event_id)
        )
        doc_ref.set(event.model_dump(mode="json"))

    def get_events(self, mission_id: str) -> list[KernelEvent]:
        snaps = (
            self.client.collection("missions").document(mission_id).collection("events").stream()
        )
        return [KernelEvent.model_validate(s.to_dict()) for s in snaps if s.to_dict()]

    # --- 5. AGENTS ---

    def save_agent_state(self, mission_id: str, agent_id: str, agent_state: dict[str, Any]) -> None:
        doc_ref = (
            self.client.collection("missions")
            .document(mission_id)
            .collection("agents")
            .document(agent_id)
        )
        doc_ref.set(agent_state)

    def get_agent_state(self, mission_id: str, agent_id: str) -> dict[str, Any] | None:
        doc_ref = (
            self.client.collection("missions")
            .document(mission_id)
            .collection("agents")
            .document(agent_id)
        )
        snap = doc_ref.get()
        return snap.to_dict() if snap.exists else None

    def list_agent_states(self, mission_id: str) -> list[dict[str, Any]]:
        snaps = (
            self.client.collection("missions").document(mission_id).collection("agents").stream()
        )
        res: list[dict[str, Any]] = []
        for s in snaps:
            d = s.to_dict()
            if d is not None:
                res.append(d)
        return res

    # --- 6. CLAIMS ---

    def save_claim(self, claim: EvidenceClaim) -> None:
        doc_ref = (
            self.client.collection("missions")
            .document(claim.mission_id)
            .collection("claims")
            .document(claim.claim_id)
        )
        doc_ref.set(claim.model_dump(mode="json"))

    def get_claim(self, mission_id: str, claim_id: str) -> EvidenceClaim | None:
        doc_ref = (
            self.client.collection("missions")
            .document(mission_id)
            .collection("claims")
            .document(claim_id)
        )
        snap = doc_ref.get()
        if not snap.exists or not snap.to_dict():
            return None
        return EvidenceClaim.model_validate(snap.to_dict())

    def list_claims(self, mission_id: str) -> list[EvidenceClaim]:
        snaps = (
            self.client.collection("missions").document(mission_id).collection("claims").stream()
        )
        return [EvidenceClaim.model_validate(s.to_dict()) for s in snaps if s.to_dict()]

    # --- 7. EVIDENCE ---

    def save_evidence(self, mission_id: str, evidence: EvidenceItem) -> None:
        doc_ref = (
            self.client.collection("missions")
            .document(mission_id)
            .collection("evidence")
            .document(evidence.evidence_id)
        )
        doc_ref.set(evidence.model_dump(mode="json"))

    def get_evidence(self, mission_id: str, evidence_id: str) -> EvidenceItem | None:
        doc_ref = (
            self.client.collection("missions")
            .document(mission_id)
            .collection("evidence")
            .document(evidence_id)
        )
        snap = doc_ref.get()
        if not snap.exists or not snap.to_dict():
            return None
        return EvidenceItem.model_validate(snap.to_dict())

    def list_evidence(self, mission_id: str) -> list[EvidenceItem]:
        snaps = (
            self.client.collection("missions").document(mission_id).collection("evidence").stream()
        )
        return [EvidenceItem.model_validate(s.to_dict()) for s in snaps if s.to_dict()]

    # --- 8. RESOURCES ---

    def save_resource_snapshot(self, mission_id: str, snapshot: dict[str, Any]) -> None:
        doc_ref = (
            self.client.collection("missions")
            .document(mission_id)
            .collection("resources")
            .document("snapshot")
        )
        doc_ref.set(snapshot)

    def get_resource_snapshot(self, mission_id: str) -> dict[str, Any] | None:
        doc_ref = (
            self.client.collection("missions")
            .document(mission_id)
            .collection("resources")
            .document("snapshot")
        )
        snap = doc_ref.get()
        return snap.to_dict() if snap.exists else None

    # --- 9. APPROVALS ---

    def save_approval(self, approval_id: str, approval_data: dict[str, Any]) -> None:
        doc_ref = self.client.collection("approvals").document(approval_id)
        doc_ref.set(approval_data)

    def get_approval(self, approval_id: str) -> dict[str, Any] | None:
        doc_ref = self.client.collection("approvals").document(approval_id)
        snap = doc_ref.get()
        return snap.to_dict() if snap.exists else None

    def list_approvals(self, status: str | None = None) -> list[dict[str, Any]]:
        query = self.client.collection("approvals")
        if status:
            query = query.where("status", "==", status)
        snaps = query.stream()
        res: list[dict[str, Any]] = []
        for s in snaps:
            d = s.to_dict()
            if d is not None:
                res.append(d)
        return res

    # --- 10. ARTIFACTS ---

    def save_artifact(
        self, mission_id: str, artifact_id: str, artifact_data: dict[str, Any]
    ) -> None:
        doc_ref = (
            self.client.collection("missions")
            .document(mission_id)
            .collection("artifacts")
            .document(artifact_id)
        )
        doc_ref.set(artifact_data)

    def get_artifact(self, mission_id: str, artifact_id: str) -> dict[str, Any] | None:
        doc_ref = (
            self.client.collection("missions")
            .document(mission_id)
            .collection("artifacts")
            .document(artifact_id)
        )
        snap = doc_ref.get()
        return snap.to_dict() if snap.exists else None

    def list_artifacts(self, mission_id: str) -> list[dict[str, Any]]:
        snaps = (
            self.client.collection("missions").document(mission_id).collection("artifacts").stream()
        )
        res: list[dict[str, Any]] = []
        for s in snaps:
            d = s.to_dict()
            if d is not None:
                res.append(d)
        return res

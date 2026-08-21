"""Agent-X Central API Runtime State Container."""

import threading
from typing import Any
from uuid import uuid4

from agentx.evidence.engine import EvidenceEngine
from agentx.kernel.events import EventBus
from agentx.kernel.models import Goal, Mission, MissionState
from agentx.kernel.workflow import Workflow
from agentx.recovery.engine import RecoveryEngine
from agentx.resource_brain.brain import ResourceBrain
from agentx_common.schemas import MissionBudget, MissionStatus


class PendingApproval:
    """Represents a Human-in-the-Loop approval awaiting operator decision."""

    def __init__(
        self,
        approval_id: str,
        mission_id: str,
        task_id: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.approval_id = approval_id
        self.mission_id = mission_id
        self.task_id = task_id
        self.reason = reason
        self.details = details or {}
        self.status = "PENDING"  # "PENDING" | "APPROVED" | "REJECTED"
        self.decision_notes: str | None = None


class ApiStateManager:
    """Thread-safe in-memory state store for managing missions, workflows, resources, evidence, and recovery."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.event_bus = EventBus()
        self.missions: dict[str, Mission] = {}
        self.workflows: dict[str, Workflow] = {}
        self.resource_brains: dict[str, ResourceBrain] = {}
        self.evidence_engines: dict[str, EvidenceEngine] = {}
        self.recovery_engines: dict[str, RecoveryEngine] = {}
        self.artifacts: dict[str, list[dict[str, Any]]] = {}  # mission_id -> list of artifact dicts
        self.approvals: dict[str, PendingApproval] = {}

    def create_mission(
        self,
        title: str,
        goal_statement: str,
        max_usd_budget: float = 5.00,
        max_runtime_minutes: int = 60,
        deliverables: list[str] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> Mission:
        """Initializes and registers a new mission with its corresponding workflow, resource brain, and evidence engine."""
        mission_id = f"msn_{uuid4().hex[:12]}"
        budget = MissionBudget(
            max_usd_limit=max_usd_budget,
            max_execution_time_seconds=max_runtime_minutes * 60,
        )
        goal = Goal(
            goal_statement=goal_statement,
            primary_objective=title,
            deliverables=deliverables or ["verified_outcome.json"],
            constraints=constraints or {},
        )
        mission = Mission(
            mission_id=mission_id,
            title=title,
            goal=goal,
            budget=budget,
            state=MissionState(status=MissionStatus.READY),
        )

        workflow = Workflow(mission_id=mission_id, event_bus=self.event_bus)
        resource_brain = ResourceBrain(
            mission_id=mission_id,
            budget=budget,
            deadline_seconds=max_runtime_minutes * 60,
            event_bus=self.event_bus,
        )
        evidence_engine = EvidenceEngine()
        recovery_engine = RecoveryEngine(event_bus=self.event_bus)

        with self._lock:
            self.missions[mission_id] = mission
            self.workflows[mission_id] = workflow
            self.resource_brains[mission_id] = resource_brain
            self.evidence_engines[mission_id] = evidence_engine
            self.recovery_engines[mission_id] = recovery_engine
            self.artifacts[mission_id] = []

        return mission

    def get_mission(self, mission_id: str) -> Mission | None:
        with self._lock:
            return self.missions.get(mission_id)

    def get_workflow(self, mission_id: str) -> Workflow | None:
        with self._lock:
            return self.workflows.get(mission_id)

    def get_resource_brain(self, mission_id: str) -> ResourceBrain | None:
        with self._lock:
            return self.resource_brains.get(mission_id)

    def get_evidence_engine(self, mission_id: str) -> EvidenceEngine | None:
        with self._lock:
            return self.evidence_engines.get(mission_id)

    def get_recovery_engine(self, mission_id: str) -> RecoveryEngine | None:
        with self._lock:
            if mission_id not in self.recovery_engines and mission_id in self.missions:
                self.recovery_engines[mission_id] = RecoveryEngine(event_bus=self.event_bus)
            return self.recovery_engines.get(mission_id)

    def register_approval(
        self,
        mission_id: str,
        task_id: str,
        reason: str,
        approval_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> PendingApproval:
        app_id = approval_id or f"app_{uuid4().hex[:8]}"
        approval = PendingApproval(
            approval_id=app_id,
            mission_id=mission_id,
            task_id=task_id,
            reason=reason,
            details=details,
        )
        with self._lock:
            self.approvals[app_id] = approval
        return approval

    def get_approval(self, approval_id: str) -> PendingApproval | None:
        with self._lock:
            return self.approvals.get(approval_id)


# Global singleton instance for FastAPI dependencies
state_manager = ApiStateManager()

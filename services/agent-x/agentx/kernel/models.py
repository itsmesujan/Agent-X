"""Agent-X Kernel Core Domain Models."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from agentx_common.schemas import (
    AgentRole,
    MissionBudget,
    MissionStatus,
    TaskStatus,
    VerificationLevel,
)


class SuccessCriteria(BaseModel):
    """Observable, testable success criterion for a mission or task."""

    model_config = ConfigDict(extra="forbid")

    criteria_id: str = Field(default_factory=lambda: f"crit_{uuid4().hex[:8]}")
    description: str = Field(..., min_length=3, description="Observable requirement statement")
    verification_level: VerificationLevel = Field(
        default=VerificationLevel.LEVEL_4_SEMANTIC,
        description="Proof hierarchy tier required to certify this criterion",
    )
    expected_metric: dict[str, Any] | None = Field(
        default=None, description="Optional key-value expected metric or assertion target"
    )
    is_satisfied: bool = Field(default=False, description="Evaluation pass state")
    evidence_uri: str | None = Field(default=None, description="GCS URI to verification proof")
    evaluation_notes: str | None = Field(default=None, description="Auditor evaluation summary")


class Goal(BaseModel):
    """Structured mission goal contract deconstructed from user intent."""

    model_config = ConfigDict(extra="forbid")

    goal_statement: str = Field(..., min_length=5, description="High-level natural language intent")
    primary_objective: str = Field(..., min_length=5, description="Concrete technical objective")
    deliverables: list[str] = Field(
        default_factory=lambda: ["verified_mission_outcome"],
        description="List of expected files, PRs, or data outputs",
    )
    constraints: dict[str, Any] = Field(
        default_factory=dict, description="Operational boundaries (e.g. read-only, max cost)"
    )
    success_criteria: list[SuccessCriteria] = Field(
        default_factory=list, description="List of verifiable success conditions"
    )


class Task(BaseModel):
    """An individual unit of work within the Mission Task DAG."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(default_factory=lambda: f"task_{uuid4().hex[:8]}")
    mission_id: str = Field(..., description="Parent mission identifier")
    name: str = Field(..., min_length=3, description="Human-readable task title")
    description: str = Field(..., description="Detailed task instructions and scope")
    agent_role: AgentRole = Field(..., description="Specialized subagent persona assigned")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current execution state")
    dependencies: list[str] = Field(
        default_factory=list, description="List of prerequisite task IDs"
    )
    dependent_children: list[str] = Field(
        default_factory=list, description="Downstream task IDs dependent on this node"
    )
    inputs: dict[str, Any] = Field(default_factory=dict, description="Resolved input arguments")
    outputs: dict[str, Any] = Field(default_factory=dict, description="Execution result payload")
    expected_outputs: list[str] = Field(
        default_factory=list, description="Filenames or artifact keys expected from tool execution"
    )
    idempotency_key: str = Field(
        default="", description="Cryptographic hash of task inputs and role"
    )
    retry_count: int = Field(default=0, ge=0, description="Number of attempted retries")
    max_retries: int = Field(default=3, ge=0, description="Max retry attempts before failing")
    timeout_seconds: int = Field(default=300, gt=0, description="Task execution timeout in seconds")
    allocated_tokens: int = Field(default=50000, gt=0, description="Max token budget for task")
    verification_level: VerificationLevel = Field(
        default=VerificationLevel.LEVEL_3_ARTIFACT, description="Target proof standard"
    )
    evidence_uri: str | None = Field(default=None, description="GCS path to verification proof")
    error_message: str | None = Field(default=None, description="Last error diagnostic message")
    locked_by_worker_id: str | None = Field(
        default=None, description="Worker ID holding the execution lease"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)

    def compute_idempotency_key(self) -> str:
        """Compute the deterministic idempotency key for this task."""
        payload = f"{self.mission_id}:{self.name}:{self.agent_role.value}:{json.dumps(self.inputs, sort_keys=True)}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def model_post_init(self, __context: Any) -> None:
        """Generate deterministic idempotency key if not provided."""
        if not self.idempotency_key:
            self.idempotency_key = self.compute_idempotency_key()

    @property
    def is_terminal(self) -> bool:
        """Returns true if the task is in a terminal state."""
        return self.status in (TaskStatus.VERIFIED, TaskStatus.SKIPPED)

    @property
    def is_failed(self) -> bool:
        """Returns true if the task has failed."""
        return self.status == TaskStatus.FAILED

    @property
    def is_unblocked(self) -> bool:
        """Returns true if the task has no unfinished dependencies."""
        return len(self.dependencies) == 0


class MissionState(BaseModel):
    """Encapsulates the lifecycle status, history, and transition metadata of a Mission."""

    model_config = ConfigDict(extra="forbid")

    status: MissionStatus = Field(default=MissionStatus.DRAFT)
    previous_status: MissionStatus | None = Field(default=None)
    transition_count: int = Field(default=0, ge=0)
    error_reason: str | None = Field(default=None)
    last_transition_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Mission(BaseModel):
    """The master root domain entity representing an autonomous operational mission."""

    model_config = ConfigDict(extra="forbid")

    mission_id: str = Field(default_factory=lambda: f"msn_{uuid4().hex[:12]}")
    title: str = Field(..., min_length=3, max_length=200, description="Mission title")
    goal: Goal = Field(..., description="Deconstructed mission goal contract")
    state: MissionState = Field(default_factory=MissionState, description="Mission state tracking")
    budget: MissionBudget = Field(
        default_factory=MissionBudget, description="Mission resource brain budget"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary user or environment metadata"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = Field(default=None)

    @property
    def status(self) -> MissionStatus:
        return self.state.status

    @property
    def is_active(self) -> bool:
        return self.status in (
            MissionStatus.PARSING_GOAL,
            MissionStatus.BUILDING_WORLD_MODEL,
            MissionStatus.PLANNING,
            MissionStatus.ALLOCATING_RESOURCES,
            MissionStatus.READY,
            MissionStatus.EXECUTING,
        )

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            MissionStatus.COMPLETED,
            MissionStatus.FAILED,
            MissionStatus.ABORTED,
        )

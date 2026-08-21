"""Agent-X Common Data Models and Schemas."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MissionStatus(StrEnum):
    DRAFT = "DRAFT"
    PARSING_GOAL = "PARSING_GOAL"
    BUILDING_WORLD_MODEL = "BUILDING_WORLD_MODEL"
    PLANNING = "PLANNING"
    ALLOCATING_RESOURCES = "ALLOCATING_RESOURCES"
    READY = "READY"
    EXECUTING = "EXECUTING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    READY = "READY"
    DISPATCHED = "DISPATCHED"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    PAUSED = "PAUSED"


class AgentRole(StrEnum):
    COORDINATOR = "COORDINATOR"
    ARCHITECT = "ARCHITECT"
    CODER = "CODER"
    TESTER = "TESTER"
    DEVOPS = "DEVOPS"
    AUDITOR = "AUDITOR"


class VerificationLevel(StrEnum):
    LEVEL_1_SYNTACTIC = "LEVEL_1_SYNTACTIC"
    LEVEL_2_EXECUTION = "LEVEL_2_EXECUTION"
    LEVEL_3_ARTIFACT = "LEVEL_3_ARTIFACT"
    LEVEL_4_SEMANTIC = "LEVEL_4_SEMANTIC"


class EpistemicState(StrEnum):
    KNOWN_FACT = "KNOWN_FACT"
    INFERRED_ASSUMPTION = "INFERRED_ASSUMPTION"
    CRITICAL_UNKNOWN = "CRITICAL_UNKNOWN"


class SuccessCriteriaDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criteria_id: str
    description: str
    verification_level: VerificationLevel = VerificationLevel.LEVEL_4_SEMANTIC
    expected_metric: dict[str, Any] | None = None
    is_satisfied: bool = False
    evidence_uri: str | None = None
    evaluation_notes: str | None = None


class GoalDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_statement: str
    primary_objective: str
    deliverables: list[str] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    success_criteria: list[SuccessCriteriaDTO] = Field(default_factory=list)


class MissionBudget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_usd_limit: float = Field(default=5.00, ge=0.0)
    max_total_tokens: int = Field(default=1_000_000, ge=0)
    max_execution_time_seconds: int = Field(default=3600, ge=0)
    current_usd_spent: float = Field(default=0.0, ge=0.0)
    current_tokens_used: int = Field(default=0, ge=0)
    current_execution_time_seconds: int = Field(default=0, ge=0)


class TaskNodeDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    mission_id: str
    name: str
    description: str
    agent_role: AgentRole
    status: TaskStatus = TaskStatus.PENDING
    dependencies: list[str] = Field(default_factory=list)
    dependent_children: list[str] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    expected_outputs: list[str] = Field(default_factory=list)
    idempotency_key: str
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300
    allocated_tokens: int = 50000
    verification_level: VerificationLevel = VerificationLevel.LEVEL_3_ARTIFACT
    evidence_uri: str | None = None
    error_message: str | None = None
    locked_by_worker_id: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class WorldModelEntityDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str
    mission_id: str
    entity_type: str
    name: str
    properties: dict[str, Any] = Field(default_factory=dict)
    epistemic_state: EpistemicState
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_uri: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

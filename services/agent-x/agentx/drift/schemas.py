"""Agent-X Goal Drift Detection Schemas and Domain Models."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class DriftSeverity(StrEnum):
    """Classification of goal drift severity."""

    ALIGNED = "ALIGNED"  # Task directly serves mission goal
    MODERATE_DRIFT = "MODERATE_DRIFT"  # Tangential or low relevance work
    CRITICAL_DRIFT = "CRITICAL_DRIFT"  # Completely out-of-scope or contradictory work


class DriftRemediationAction(StrEnum):
    """The 5 goal drift remediation actions supported by Agent-X."""

    FLAG = "FLAG"  # Mark task metadata without altering DAG state
    PAUSE = "PAUSE"  # Pause task execution in the workflow
    CANCEL = "CANCEL"  # Cancel/skip the drifted task
    REPLACE = "REPLACE"  # Replace drifted task with an aligned substitute
    REPRIORITIZE = "REPRIORITIZE"  # Deprioritize task to back of execution queue


class TaskRelevanceReport(BaseModel):
    """Relevance and goal alignment report for an individual task."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(default_factory=lambda: f"drf_{uuid4().hex[:10]}")
    task_id: str
    mission_id: str
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Composite alignment score")
    semantic_similarity: float = Field(..., ge=0.0, le=1.0)
    deliverable_contribution: float = Field(..., ge=0.0, le=1.0)
    severity: DriftSeverity
    explanation: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DriftEvaluationResult(BaseModel):
    """Workflow-wide drift evaluation report comparing active DAG against original mission."""

    model_config = ConfigDict(extra="forbid")

    evaluation_id: str = Field(default_factory=lambda: f"dfr_{uuid4().hex[:10]}")
    mission_id: str
    overall_drift_score: float = Field(
        ..., ge=0.0, le=1.0, description="Average workflow alignment"
    )
    task_reports: list[TaskRelevanceReport] = Field(default_factory=list)
    drifted_task_count: int = Field(default=0, ge=0)
    recommended_remediations: dict[str, DriftRemediationAction] = Field(
        default_factory=dict, description="Task ID -> Recommended DriftRemediationAction"
    )
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DriftRemediationRecord(BaseModel):
    """Audit record of a goal drift remediation applied to a workflow."""

    model_config = ConfigDict(extra="forbid")

    remediation_id: str = Field(default_factory=lambda: f"rem_{uuid4().hex[:10]}")
    mission_id: str
    task_id: str
    action: DriftRemediationAction
    reason: str
    details: dict[str, Any] = Field(default_factory=dict)
    applied_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

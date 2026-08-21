"""Agent-X Goal Engine Data Contracts and Schemas."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agentx.kernel.models import SuccessCriteria
from agentx_common.schemas import MissionBudget


class RiskLevel(StrEnum):
    """Mission operational and security risk categorization."""

    LOW = "LOW"  # Read-only inspection, reporting, static linting
    MEDIUM = "MEDIUM"  # Code editing, unit test execution in sandbox
    HIGH = "HIGH"  # Build generation, package installation, multi-file refactoring
    CRITICAL = "CRITICAL"  # Infrastructure provisioning, IAM modifications, destructive operations


class RequiredCapability(StrEnum):
    """Subagent specialized capabilities required to execute a mission."""

    CODE_ANALYSIS = "CODE_ANALYSIS"
    CODE_GENERATION = "CODE_GENERATION"
    SHELL_EXECUTION = "SHELL_EXECUTION"
    TERRAFORM_PROVISIONING = "TERRAFORM_PROVISIONING"
    SECURITY_AUDIT = "SECURITY_AUDIT"
    CONTAINER_BUILD = "CONTAINER_BUILD"
    TEST_EXECUTION = "TEST_EXECUTION"
    EVALUATION_BENCHMARK = "EVALUATION_BENCHMARK"
    WEB_RESEARCH = "WEB_RESEARCH"


class MalformedMissionError(Exception):
    """Raised when natural language mission input is malformed, empty, or violates safety invariants."""

    pass


class GoalInputOverrides(BaseModel):
    """User-specified explicit parameter overrides when creating a mission."""

    model_config = ConfigDict(extra="forbid")

    max_usd_budget: float | None = Field(default=None, ge=0.1, le=100.0)
    max_runtime_minutes: int | None = Field(default=None, ge=1, le=1440)
    initial_constraints: dict[str, Any] = Field(default_factory=dict)
    required_deliverables: list[str] = Field(default_factory=list)


class ParsedGoalOutput(BaseModel):
    """Structured, verified goal contract produced by the Goal Engine."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=3, max_length=150, description="Concise mission title")
    goal_statement: str = Field(
        ..., min_length=5, description="High-level natural language intent formulation"
    )
    primary_objective: str = Field(..., min_length=5, description="Concrete technical objective")
    deliverables: list[str] = Field(
        default_factory=lambda: ["verified_mission_outcome"],
        description="Explicit deliverables (files, PRs, diffs, reports)",
    )
    constraints: dict[str, Any] = Field(
        default_factory=dict, description="Operational boundaries and safety constraints"
    )
    budget: MissionBudget = Field(default_factory=MissionBudget)
    deadline_seconds: int = Field(default=3600, ge=60, le=86400)
    success_criteria: list[SuccessCriteria] = Field(
        default_factory=list, description="Observable acceptance criteria"
    )
    risk_level: RiskLevel = Field(default=RiskLevel.MEDIUM)
    risk_summary: str = Field(..., description="Justification for assigned risk level")
    required_capabilities: list[RequiredCapability] = Field(
        default_factory=list, description="List of required subagent skills"
    )

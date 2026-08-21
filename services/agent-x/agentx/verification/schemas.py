"""Agent-X Verification Engine Schemas and Evaluation Models."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class VerificationOutcome(StrEnum):
    """Overall outcome of a verification evaluation."""

    PASS = "PASS"
    FAIL = "FAIL"
    REPAIR_REQUIRED = "REPAIR_REQUIRED"


class VerificationDimension(StrEnum):
    """The 7 mandatory verification dimensions of Agent-X."""

    SUCCESS_CRITERIA = "SUCCESS_CRITERIA"
    REQUIREMENTS = "REQUIREMENTS"
    CLAIMS = "CLAIMS"
    EVIDENCE = "EVIDENCE"
    CONSISTENCY = "CONSISTENCY"
    ARTIFACT_COMPLETENESS = "ARTIFACT_COMPLETENESS"
    RISK_CONDITIONS = "RISK_CONDITIONS"


class CheckResult(BaseModel):
    """Result of an individual deterministic verification check."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Name or identifier of the check")
    dimension: VerificationDimension = Field(..., description="Target verification dimension")
    passed: bool = Field(..., description="Whether this check passed")
    is_critical: bool = Field(
        default=True, description="If True, failure triggers FAIL or REPAIR_REQUIRED"
    )
    details: str = Field(..., description="Diagnostic explanation of the result")
    expected_value: Any = Field(default=None, description="Expected value or threshold")
    measured_value: Any = Field(default=None, description="Actual observed value")


class DimensionEvaluation(BaseModel):
    """Aggregate evaluation for one of the 7 verification dimensions."""

    model_config = ConfigDict(extra="forbid")

    dimension: VerificationDimension
    passed: bool
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized compliance score")
    checks: list[CheckResult] = Field(default_factory=list)
    summary: str


class VerificationReport(BaseModel):
    """Formal, signed verification report certifying or rejecting mission completion."""

    model_config = ConfigDict(extra="forbid")

    verification_id: str = Field(default_factory=lambda: f"vrf_{uuid4().hex[:10]}")
    mission_id: str
    overall_outcome: VerificationOutcome
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Composite verification score")
    dimension_evaluations: dict[str, DimensionEvaluation] = Field(
        default_factory=dict, description="Dimension name -> DimensionEvaluation"
    )
    failed_checks: list[CheckResult] = Field(default_factory=list, description="All failing checks")
    repair_recommendations: list[str] = Field(
        default_factory=list, description="Targeted self-healing actions if REPAIR_REQUIRED"
    )
    evaluator_signature: str = Field(..., description="Cryptographic HMAC-SHA256 signature")
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

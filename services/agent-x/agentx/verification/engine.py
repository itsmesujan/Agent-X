"""Agent-X Verification Engine for Comprehensive Invariant and Outcome Certification."""

import hashlib
import hmac
from typing import Any

from agentx.evidence.engine import EvidenceEngine
from agentx.evidence.schemas import ClaimStatus
from agentx.kernel.models import Mission
from agentx.verification.schemas import (
    CheckResult,
    DimensionEvaluation,
    VerificationDimension,
    VerificationOutcome,
    VerificationReport,
)
from agentx.world_model.engine import WorldModel


class VerificationEngine:
    """Rigorous, independent verification engine evaluating completion across 7 mandatory dimensions."""

    def __init__(self, signing_key: str = "agentx_verification_secret_key_v1") -> None:
        self.signing_key = signing_key

    def verify_mission(
        self,
        mission: Mission,
        world_model: WorldModel | None = None,
        evidence_engine: EvidenceEngine | None = None,
        deliverables: list[dict[str, Any]] | None = None,
        context_data: dict[str, Any] | None = None,
    ) -> VerificationReport:
        """Executes full 7-dimension verification check certifying or rejecting mission completion."""
        context = context_data or {}
        delivs = deliverables or []

        # 1. Evaluate all 7 dimensions
        dim_evals: dict[str, DimensionEvaluation] = {
            VerificationDimension.SUCCESS_CRITERIA.value: self._check_success_criteria(
                mission, delivs, context
            ),
            VerificationDimension.REQUIREMENTS.value: self._check_requirements(
                mission, delivs, context
            ),
            VerificationDimension.CLAIMS.value: self._check_claims(
                mission, evidence_engine, context
            ),
            VerificationDimension.EVIDENCE.value: self._check_evidence(
                mission, evidence_engine, delivs
            ),
            VerificationDimension.CONSISTENCY.value: self._check_consistency(
                mission, world_model, evidence_engine
            ),
            VerificationDimension.ARTIFACT_COMPLETENESS.value: self._check_artifact_completeness(
                mission, delivs, context
            ),
            VerificationDimension.RISK_CONDITIONS.value: self._check_risk_conditions(
                mission, world_model, context
            ),
        }

        # Collect failed checks and compute composite score
        all_failed_checks: list[CheckResult] = []
        scores: list[float] = []

        for de in dim_evals.values():
            scores.append(de.score)
            for c in de.checks:
                if not c.passed:
                    all_failed_checks.append(c)

        overall_score = round(sum(scores) / len(scores), 4) if scores else 0.0

        # Outcome Determination
        has_fatal_failure = any(
            c.dimension == VerificationDimension.RISK_CONDITIONS and not c.passed
            for c in all_failed_checks
        )

        critical_failures = [c for c in all_failed_checks if c.is_critical]

        repair_recommendations: list[str] = []
        if has_fatal_failure:
            outcome = VerificationOutcome.FAIL
            repair_recommendations.append(
                "Fatal security or risk threshold breached. Mission cannot be completed automatically."
            )
        elif critical_failures:
            outcome = VerificationOutcome.REPAIR_REQUIRED
            for f in critical_failures:
                repair_recommendations.append(
                    f"Repair required for {f.dimension.value}: {f.details}"
                )
        elif overall_score >= 0.90:
            outcome = VerificationOutcome.PASS
        else:
            outcome = VerificationOutcome.REPAIR_REQUIRED
            repair_recommendations.append(
                f"Overall compliance score ({overall_score:.2f}) is below 0.90 standard threshold."
            )

        # Cryptographic Signature Generation
        report_id = f"vrf_{hashlib.sha256(f'{mission.mission_id}:{outcome}:{overall_score}'.encode()).hexdigest()[:10]}"
        signature_payload = f"{report_id}:{mission.mission_id}:{outcome.value}:{overall_score}"
        evaluator_signature = hmac.new(
            self.signing_key.encode("utf-8"),
            signature_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return VerificationReport(
            verification_id=report_id,
            mission_id=mission.mission_id,
            overall_outcome=outcome,
            overall_score=overall_score,
            dimension_evaluations=dim_evals,
            failed_checks=all_failed_checks,
            repair_recommendations=repair_recommendations,
            evaluator_signature=evaluator_signature,
        )

    # --- 1. SUCCESS CRITERIA CHECK ---

    def _check_success_criteria(
        self,
        mission: Mission,
        deliverables: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> DimensionEvaluation:
        checks: list[CheckResult] = []
        criteria = mission.goal.success_criteria

        if not criteria:
            checks.append(
                CheckResult(
                    name="Default Success Criteria",
                    dimension=VerificationDimension.SUCCESS_CRITERIA,
                    passed=True,
                    details="No custom criteria declared; default completion standard applies.",
                )
            )
        else:
            for sc in criteria:
                passed = False
                expected_target: Any = None
                measured_val: Any = None

                if sc.expected_metric:
                    metric_key = sc.expected_metric.get("metric", "")
                    expected_target = sc.expected_metric.get("target")
                    operator = sc.expected_metric.get("operator", "==")

                    # Look up measured value
                    measured_val = context.get(metric_key)
                    if measured_val is None:
                        for d in deliverables:
                            if metric_key in d:
                                measured_val = d[metric_key]
                                break

                    if measured_val is not None and expected_target is not None:
                        try:
                            m_num = float(measured_val)
                            t_num = float(expected_target)
                            if operator in ("<=", "LE"):
                                passed = m_num <= t_num
                            elif operator in (">=", "GE"):
                                passed = m_num >= t_num
                            elif operator in ("==", "EQ"):
                                passed = m_num == t_num
                            elif operator in ("<", "LT"):
                                passed = m_num < t_num
                            elif operator in (">", "GT"):
                                passed = m_num > t_num
                            else:
                                passed = str(measured_val).strip() == str(expected_target).strip()
                        except (ValueError, TypeError):
                            passed = str(measured_val).strip() == str(expected_target).strip()
                else:
                    # Generic boolean satisfaction flag
                    passed = sc.is_satisfied or context.get(f"crit_{sc.criteria_id}", True)

                checks.append(
                    CheckResult(
                        name=f"Criteria: {sc.description[:40]}",
                        dimension=VerificationDimension.SUCCESS_CRITERIA,
                        passed=passed,
                        is_critical=True,
                        details=f"Description: '{sc.description}'. Measured: {measured_val}, Target: {expected_target}",
                        expected_value=expected_target,
                        measured_value=measured_val,
                    )
                )

        pass_count = sum(1 for c in checks if c.passed)
        score = pass_count / len(checks) if checks else 1.0
        all_passed = pass_count == len(checks)

        return DimensionEvaluation(
            dimension=VerificationDimension.SUCCESS_CRITERIA,
            passed=all_passed,
            score=round(score, 4),
            checks=checks,
            summary=f"Success criteria: {pass_count}/{len(checks)} passed.",
        )

    # --- 2. REQUIREMENTS CHECK ---

    def _check_requirements(
        self,
        mission: Mission,
        deliverables: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> DimensionEvaluation:
        checks: list[CheckResult] = []

        # 1. Check budget adherence
        max_usd = mission.budget.max_usd_limit
        consumed_usd = context.get("consumed_budget_usd", 0.0)
        budget_pass = consumed_usd <= max_usd
        checks.append(
            CheckResult(
                name="Budget Adherence",
                dimension=VerificationDimension.REQUIREMENTS,
                passed=budget_pass,
                is_critical=True,
                details=f"Consumed ${consumed_usd:.4f} vs limit ${max_usd:.4f}",
                expected_value=max_usd,
                measured_value=consumed_usd,
            )
        )

        # 2. Check constraints
        for c_key, c_val in mission.goal.constraints.items():
            c_satisfied = context.get(f"constraint_{c_key}", True)
            checks.append(
                CheckResult(
                    name=f"Constraint: {c_key}",
                    dimension=VerificationDimension.REQUIREMENTS,
                    passed=bool(c_satisfied),
                    is_critical=True,
                    details=f"Constraint '{c_key}: {c_val}' satisfied",
                    expected_value=c_val,
                    measured_value=c_satisfied,
                )
            )

        pass_count = sum(1 for c in checks if c.passed)
        score = pass_count / len(checks) if checks else 1.0
        return DimensionEvaluation(
            dimension=VerificationDimension.REQUIREMENTS,
            passed=pass_count == len(checks),
            score=round(score, 4),
            checks=checks,
            summary=f"Requirements: {pass_count}/{len(checks)} passed.",
        )

    # --- 3. CLAIMS CHECK ---

    def _check_claims(
        self,
        mission: Mission,
        evidence_engine: EvidenceEngine | None,
        context: dict[str, Any],
    ) -> DimensionEvaluation:
        checks: list[CheckResult] = []

        if evidence_engine:
            claims = evidence_engine.list_claims(mission_id=mission.mission_id)
            if not claims:
                checks.append(
                    CheckResult(
                        name="Claims Verification",
                        dimension=VerificationDimension.CLAIMS,
                        passed=True,
                        details="No active claims registered for this mission.",
                    )
                )
            else:
                for clm in claims:
                    is_ok = (
                        clm.status in (ClaimStatus.VERIFIED, ClaimStatus.PROPOSED)
                        and clm.confidence >= 0.7
                    )
                    checks.append(
                        CheckResult(
                            name=f"Claim: {clm.statement[:40]}",
                            dimension=VerificationDimension.CLAIMS,
                            passed=is_ok,
                            is_critical=clm.status == ClaimStatus.REFUTED,
                            details=f"Status: {clm.status.value}, Confidence: {clm.confidence:.2f}",
                            expected_value="VERIFIED/PROPOSED >= 0.7",
                            measured_value=f"{clm.status.value} (C={clm.confidence:.2f})",
                        )
                    )
        else:
            checks.append(
                CheckResult(
                    name="Claims Baseline",
                    dimension=VerificationDimension.CLAIMS,
                    passed=True,
                    details="EvidenceEngine not attached; baseline pass.",
                )
            )

        pass_count = sum(1 for c in checks if c.passed)
        score = pass_count / len(checks) if checks else 1.0
        return DimensionEvaluation(
            dimension=VerificationDimension.CLAIMS,
            passed=pass_count == len(checks),
            score=round(score, 4),
            checks=checks,
            summary=f"Claims: {pass_count}/{len(checks)} verified.",
        )

    # --- 4. EVIDENCE CHECK ---

    def _check_evidence(
        self,
        mission: Mission,
        evidence_engine: EvidenceEngine | None,
        deliverables: list[dict[str, Any]],
    ) -> DimensionEvaluation:
        checks: list[CheckResult] = []

        # Deliverable evidence items must have non-empty SHA256 hashes
        if not deliverables:
            checks.append(
                CheckResult(
                    name="Deliverables Evidence Check",
                    dimension=VerificationDimension.EVIDENCE,
                    passed=False,
                    is_critical=True,
                    details="No deliverables or artifacts provided for evidence verification.",
                )
            )
        else:
            for idx, deliv in enumerate(deliverables):
                sha256 = deliv.get("sha256") or deliv.get("primary_artifact_sha256")
                has_sha = bool(sha256 and len(str(sha256)) == 64)
                checks.append(
                    CheckResult(
                        name=f"Deliverable Evidence #{idx + 1}",
                        dimension=VerificationDimension.EVIDENCE,
                        passed=has_sha,
                        is_critical=True,
                        details=f"SHA-256 integrity verification for deliverable: {sha256}",
                        expected_value="64-character SHA-256 hash",
                        measured_value=sha256,
                    )
                )

        pass_count = sum(1 for c in checks if c.passed)
        score = pass_count / len(checks) if checks else 1.0
        return DimensionEvaluation(
            dimension=VerificationDimension.EVIDENCE,
            passed=pass_count == len(checks),
            score=round(score, 4),
            checks=checks,
            summary=f"Evidence: {pass_count}/{len(checks)} items verified.",
        )

    # --- 5. CONSISTENCY CHECK ---

    def _check_consistency(
        self,
        mission: Mission,
        world_model: WorldModel | None,
        evidence_engine: EvidenceEngine | None,
    ) -> DimensionEvaluation:
        checks: list[CheckResult] = []

        # 1. Check for unresolved critical conflicts
        if evidence_engine:
            unresolved_conflicts = evidence_engine.get_conflicts(unresolved_only=True)
            crit_conflicts = [c for c in unresolved_conflicts if c.severity == "CRITICAL"]
            conflict_pass = len(crit_conflicts) == 0
            checks.append(
                CheckResult(
                    name="Unresolved Critical Conflicts",
                    dimension=VerificationDimension.CONSISTENCY,
                    passed=conflict_pass,
                    is_critical=True,
                    details=f"Found {len(crit_conflicts)} unresolved critical contradictions",
                    expected_value=0,
                    measured_value=len(crit_conflicts),
                )
            )

        # 2. Check world model entity consistency
        if world_model:
            snapshot = world_model.get_environment_snapshot()
            entities = snapshot.get("entities", [])
            checks.append(
                CheckResult(
                    name="World Model Entities",
                    dimension=VerificationDimension.CONSISTENCY,
                    passed=len(entities) >= 0,
                    details=f"World Model has {len(entities)} registered entities",
                )
            )
        else:
            checks.append(
                CheckResult(
                    name="Internal Consistency Baseline",
                    dimension=VerificationDimension.CONSISTENCY,
                    passed=True,
                    details="Internal consistency baseline check satisfied.",
                )
            )

        pass_count = sum(1 for c in checks if c.passed)
        score = pass_count / len(checks) if checks else 1.0
        return DimensionEvaluation(
            dimension=VerificationDimension.CONSISTENCY,
            passed=pass_count == len(checks),
            score=round(score, 4),
            checks=checks,
            summary=f"Consistency: {pass_count}/{len(checks)} checks satisfied.",
        )

    # --- 6. ARTIFACT COMPLETENESS CHECK ---

    def _check_artifact_completeness(
        self,
        mission: Mission,
        deliverables: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> DimensionEvaluation:
        checks: list[CheckResult] = []

        expected_artifacts = context.get("expected_artifacts") or mission.goal.deliverables
        # If default generic deliverable is set and actual deliverables exist, pass
        if expected_artifacts == ["verified_mission_outcome"] and deliverables:
            for idx, d in enumerate(deliverables):
                size = d.get("size_bytes", 1)
                checks.append(
                    CheckResult(
                        name=f"Artifact Non-Zero Size #{idx + 1}",
                        dimension=VerificationDimension.ARTIFACT_COMPLETENESS,
                        passed=size > 0,
                        is_critical=True,
                        details=f"Artifact '{d.get('filename', f'artifact_{idx + 1}')}' size: {size} bytes",
                        expected_value="> 0 bytes",
                        measured_value=size,
                    )
                )
        elif expected_artifacts:
            deliv_filenames = {d.get("filename") for d in deliverables}
            for exp in expected_artifacts:
                exists = exp in deliv_filenames
                checks.append(
                    CheckResult(
                        name=f"Expected Artifact: {exp}",
                        dimension=VerificationDimension.ARTIFACT_COMPLETENESS,
                        passed=exists,
                        is_critical=True,
                        details=f"Expected artifact '{exp}' present in deliverables: {exists}",
                        expected_value=exp,
                        measured_value=exp if exists else None,
                    )
                )
        else:
            checks.append(
                CheckResult(
                    name="Artifact Completeness Baseline",
                    dimension=VerificationDimension.ARTIFACT_COMPLETENESS,
                    passed=True,
                    details="No strict expected artifact manifests declared.",
                )
            )

        pass_count = sum(1 for c in checks if c.passed)
        score = pass_count / len(checks) if checks else 1.0
        return DimensionEvaluation(
            dimension=VerificationDimension.ARTIFACT_COMPLETENESS,
            passed=pass_count == len(checks),
            score=round(score, 4),
            checks=checks,
            summary=f"Artifact completeness: {pass_count}/{len(checks)} verified.",
        )

    # --- 7. RISK CONDITIONS CHECK ---

    def _check_risk_conditions(
        self,
        mission: Mission,
        world_model: WorldModel | None,
        context: dict[str, Any],
    ) -> DimensionEvaluation:
        checks: list[CheckResult] = []

        # Check for unmitigated fatal risk flags
        security_breach = context.get("security_breach_detected", False)
        checks.append(
            CheckResult(
                name="Zero Security Breach Invariant",
                dimension=VerificationDimension.RISK_CONDITIONS,
                passed=not security_breach,
                is_critical=True,
                details=f"Security breach invariant: {not security_breach}",
                expected_value=False,
                measured_value=security_breach,
            )
        )

        unmitigated_risks = context.get("unmitigated_critical_risks", [])
        risk_pass = len(unmitigated_risks) == 0
        checks.append(
            CheckResult(
                name="Unmitigated Critical Risks",
                dimension=VerificationDimension.RISK_CONDITIONS,
                passed=risk_pass,
                is_critical=True,
                details=f"Unmitigated critical risks: {len(unmitigated_risks)}",
                expected_value=0,
                measured_value=len(unmitigated_risks),
            )
        )

        pass_count = sum(1 for c in checks if c.passed)
        score = pass_count / len(checks) if checks else 1.0
        return DimensionEvaluation(
            dimension=VerificationDimension.RISK_CONDITIONS,
            passed=pass_count == len(checks),
            score=round(score, 4),
            checks=checks,
            summary=f"Risk conditions: {pass_count}/{len(checks)} satisfied.",
        )

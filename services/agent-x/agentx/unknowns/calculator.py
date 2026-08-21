"""Agent-X Unknowns Priority Calculator with Explainable Justification."""

from agentx.unknowns.schemas import EpistemicUnknown, PriorityBreakdown, PriorityTier

WEIGHT_IMPACT = 0.35
WEIGHT_DECISION_RELEVANCE = 0.25
WEIGHT_UNCERTAINTY = 0.20
WEIGHT_URGENCY = 0.15
WEIGHT_COST_DISCOUNT = 0.05

TASK_CONVERSION_THRESHOLD = 50.0


def calculate_dynamic_urgency(
    base_urgency: float,
    deadline_remaining_ratio: float | None = None,
    blocked_tasks_count: int = 0,
) -> float:
    """Calculate dynamic urgency adjusted for deadline pressure and blocked downstream tasks."""
    urgency = base_urgency

    # Apply deadline pressure
    if deadline_remaining_ratio is not None:
        if deadline_remaining_ratio <= 0.15:  # Critical time crunch (<15% remaining)
            urgency += 0.35
        elif deadline_remaining_ratio <= 0.35:  # High time pressure (<35% remaining)
            urgency += 0.20
        elif deadline_remaining_ratio <= 0.50:  # Moderate pressure (<50% remaining)
            urgency += 0.10

    # Apply blocker multiplier
    if blocked_tasks_count > 0:
        urgency += min(0.30, 0.10 * blocked_tasks_count)

    return min(1.0, max(0.0, urgency))


def evaluate_unknown_priority(
    unknown: EpistemicUnknown,
    deadline_remaining_ratio: float | None = None,
    conversion_threshold: float = TASK_CONVERSION_THRESHOLD,
) -> PriorityBreakdown:
    """Calculate an explainable, transparent priority score for an unknown."""
    if unknown.is_resolved:
        return PriorityBreakdown(
            priority_score=0.0,
            tier=PriorityTier.LOW,
            weighted_impact=0.0,
            weighted_uncertainty=0.0,
            weighted_decision_relevance=0.0,
            weighted_urgency=0.0,
            cost_discount_bonus=0.0,
            explanation=f"Unknown '{unknown.unknown_id}' is already resolved by fact '{unknown.resolved_fact_id}'. Priority is 0.",
            should_convert_to_task=False,
        )

    # 1. Compute dynamic urgency considering deadline and blockers
    effective_urgency = calculate_dynamic_urgency(
        base_urgency=unknown.urgency,
        deadline_remaining_ratio=deadline_remaining_ratio,
        blocked_tasks_count=len(unknown.blocking_task_ids),
    )

    # 2. Weighted score components [0.0 - 100.0]
    w_impact = unknown.impact * WEIGHT_IMPACT * 100.0
    w_decision = unknown.decision_relevance * WEIGHT_DECISION_RELEVANCE * 100.0
    w_uncertainty = unknown.uncertainty * WEIGHT_UNCERTAINTY * 100.0
    w_urgency = effective_urgency * WEIGHT_URGENCY * 100.0
    cost_discount = (1.0 - unknown.research_cost) * WEIGHT_COST_DISCOUNT * 100.0

    raw_score = w_impact + w_decision + w_uncertainty + w_urgency + cost_discount
    final_score = round(min(100.0, max(0.0, raw_score)), 1)

    # 3. Categorize into Priority Tier
    if final_score >= 80.0:
        tier = PriorityTier.CRITICAL
    elif final_score >= 65.0:
        tier = PriorityTier.HIGH
    elif final_score >= 45.0:
        tier = PriorityTier.MEDIUM
    else:
        tier = PriorityTier.LOW

    # 4. Generate Explainable Justification
    reasons: list[str] = []
    if unknown.impact >= 0.8:
        reasons.append(f"high failure impact ({unknown.impact:.2f})")
    elif unknown.impact <= 0.3:
        reasons.append(f"low mission impact ({unknown.impact:.2f})")

    if unknown.decision_relevance >= 0.7:
        reasons.append(
            f"critical architectural branching relevance ({unknown.decision_relevance:.2f})"
        )

    if len(unknown.blocking_task_ids) > 0:
        reasons.append(f"blocking {len(unknown.blocking_task_ids)} downstream task(s)")

    if deadline_remaining_ratio is not None and deadline_remaining_ratio <= 0.35:
        reasons.append(
            f"severe deadline pressure ({deadline_remaining_ratio * 100:.0f}% time remaining)"
        )

    if unknown.research_cost <= 0.2:
        reasons.append("low research cost (quick exploration win)")

    reasons_str = ", ".join(reasons) if reasons else "baseline assessment factors"
    explanation = (
        f"Priority Score: {final_score}/100 [{tier.value}]. "
        f"Driven by: {reasons_str}. "
        f"(Impact: {w_impact:.1f}, Relevance: {w_decision:.1f}, Uncertainty: {w_uncertainty:.1f}, "
        f"Urgency: {w_urgency:.1f}, Cheap-discovery bonus: +{cost_discount:.1f})"
    )

    should_convert = final_score >= conversion_threshold and not unknown.is_resolved

    return PriorityBreakdown(
        priority_score=final_score,
        tier=tier,
        weighted_impact=round(w_impact, 2),
        weighted_uncertainty=round(w_uncertainty, 2),
        weighted_decision_relevance=round(w_decision, 2),
        weighted_urgency=round(w_urgency, 2),
        cost_discount_bonus=round(cost_discount, 2),
        explanation=explanation,
        should_convert_to_task=should_convert,
    )

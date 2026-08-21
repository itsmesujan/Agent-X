"""Agent-X Strategy Selector with Multi-Criteria Utility Optimization."""

from agentx.planning.schemas import (
    CandidateStrategy,
    PlanningContext,
    ScoredStrategy,
    StrategySelectionCriteria,
    StrategySelectionResult,
)


class StrategySelector:
    """Evaluates, filters, scores, and selects the optimal candidate strategy for a mission."""

    def evaluate_strategy(
        self,
        strategy: CandidateStrategy,
        context: PlanningContext,
        criteria: StrategySelectionCriteria,
    ) -> ScoredStrategy:
        """Evaluate feasibility and calculate composite utility score for a candidate strategy."""
        rejection_reasons: list[str] = []

        max_budget = criteria.max_usd_budget or context.budget.max_usd_limit
        max_duration = criteria.max_duration_seconds or context.deadline_seconds

        # 1. Feasibility Hard Constraints
        if strategy.estimated_cost_usd > max_budget:
            rejection_reasons.append(
                f"Estimated cost ${strategy.estimated_cost_usd:.2f} exceeds budget cap ${max_budget:.2f}"
            )

        if strategy.estimated_duration_seconds > max_duration:
            rejection_reasons.append(
                f"Estimated duration {strategy.estimated_duration_seconds}s exceeds deadline {max_duration}s"
            )

        missing_capabilities = [
            role for role in strategy.required_capabilities if role not in context.available_agents
        ]
        if missing_capabilities:
            rejection_reasons.append(
                f"Required agent roles {missing_capabilities} are unavailable in agent pool"
            )

        is_feasible = len(rejection_reasons) == 0

        # 2. Utility Scoring Components
        p_success = strategy.expected_success_probability
        s_risk = strategy.risk_score
        cost_eff = 1.0 - min(1.0, strategy.estimated_cost_usd / max(0.01, max_budget))
        time_eff = 1.0 - min(1.0, strategy.estimated_duration_seconds / max(1, max_duration))

        raw_utility = (
            criteria.weight_success_probability * p_success
            - criteria.weight_risk_penalty * s_risk
            + criteria.weight_cost_efficiency * cost_eff
            + criteria.weight_speed_efficiency * time_eff
        ) * 100.0

        utility_score = round(raw_utility, 1) if is_feasible else -1000.0 + round(raw_utility, 1)

        return ScoredStrategy(
            strategy=strategy,
            utility_score=utility_score,
            is_feasible=is_feasible,
            rejection_reasons=rejection_reasons,
        )

    def select_strategy(
        self,
        candidates: list[CandidateStrategy],
        context: PlanningContext,
        criteria: StrategySelectionCriteria | None = None,
    ) -> StrategySelectionResult:
        """Score, rank, and select the optimal strategy."""
        if not candidates:
            raise ValueError("Cannot select strategy from empty candidate list")

        sel_criteria = criteria or StrategySelectionCriteria()
        scored_list: list[ScoredStrategy] = [
            self.evaluate_strategy(cand, context, sel_criteria) for cand in candidates
        ]

        # Sort descending by utility score
        ranked = sorted(scored_list, key=lambda s: s.utility_score, reverse=True)
        winner = ranked[0]

        # Generate transparent justification
        if winner.is_feasible:
            rationale = (
                f"Selected Strategy: '{winner.strategy.name}' ({winner.strategy.strategy_type.value}) "
                f"with highest utility score of {winner.utility_score:.1f}. "
                f"Expected success: {winner.strategy.expected_success_probability * 100:.0f}%, "
                f"Risk score: {winner.strategy.risk_score:.2f} ({winner.strategy.risk.value}), "
                f"Estimated cost: ${winner.strategy.estimated_cost_usd:.2f} (budget cap: ${context.budget.max_usd_limit:.2f}), "
                f"Estimated duration: {winner.strategy.estimated_duration_seconds}s ({winner.strategy.estimated_duration_seconds / 60:.1f}m)."
            )
        else:
            rationale = (
                f"WARNING: No candidate strategy fully satisfied all hard constraints. "
                f"Closest candidate '{winner.strategy.name}' selected with utility {winner.utility_score:.1f}. "
                f"Constraint violations: {'; '.join(winner.rejection_reasons)}."
            )

        return StrategySelectionResult(
            selected_strategy=winner.strategy,
            selection_rationale=rationale,
            candidates_ranked=ranked,
        )

"""Agent-X Analyst Agent."""

import math
from typing import Any

from agentx.runtime.base import BaseAgent
from agentx.runtime.schemas import AgentInvocationContext, AgentType


class AnalystAgent(BaseAgent):
    """Specialized agent for quantitative evaluation, metric calculation, and risk assessment."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            agent_type=AgentType.ANALYST,
            name="AnalystAgent",
            description="Computes metrics, evaluates tradeoffs, and performs risk analysis.",
            capabilities=["analysis"],
            **kwargs,
        )

    async def _execute_internal(self, context: AgentInvocationContext) -> dict[str, Any]:
        """Analyzes numeric and structural inputs, producing insights and risk scores."""
        metrics_input = context.inputs.get("metrics", {})
        data_points = context.inputs.get("data_points", [])

        # Quantitative statistical computation if data_points are provided
        stats: dict[str, Any] = {}
        if (
            isinstance(data_points, list)
            and data_points
            and all(isinstance(x, (int, float)) for x in data_points)
        ):
            count = len(data_points)
            total = sum(data_points)
            mean = total / count
            variance = sum((x - mean) ** 2 for x in data_points) / count
            std_dev = math.sqrt(variance)
            stats = {
                "count": count,
                "min": min(data_points),
                "max": max(data_points),
                "mean": round(mean, 4),
                "std_dev": round(std_dev, 4),
            }

        # Calculate risk score (0.0 to 1.0)
        risk_factors = context.inputs.get("risk_factors", [])
        base_risk = 0.2
        if isinstance(risk_factors, list):
            base_risk += min(0.6, len(risk_factors) * 0.15)

        return {
            "analysis_type": context.inputs.get("analysis_type", "GENERAL_ASSESSMENT"),
            "statistical_summary": stats,
            "evaluated_metrics": metrics_input,
            "overall_risk_score": round(base_risk, 2),
            "recommendation": "PROCEED" if base_risk < 0.5 else "PROCEED_WITH_GUARDRAILS",
            "__confidence__": 0.92,
            "__tokens_used__": 1500,
            "__cost_usd__": 0.00045,
        }

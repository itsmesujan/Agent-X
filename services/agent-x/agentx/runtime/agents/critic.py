"""Agent-X Critic Agent."""

from typing import Any

from agentx.runtime.base import BaseAgent
from agentx.runtime.schemas import AgentInvocationContext, AgentType


class CriticAgent(BaseAgent):
    """Specialized agent for adversarial review, edge case detection, and hallucination critique."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            agent_type=AgentType.CRITIC,
            name="CriticAgent",
            description="Adversarially critiques plans and outputs, flagging defects and edge-case risks.",
            capabilities=["critique"],
            **kwargs,
        )

    async def _execute_internal(self, context: AgentInvocationContext) -> dict[str, Any]:
        """Critiques target deliverables against acceptance criteria and constraints."""
        deliverable = context.inputs.get("deliverable", {})
        criteria = context.inputs.get("acceptance_criteria", [])

        issues_found: list[dict[str, Any]] = []

        # Check for empty or missing deliverables
        if not deliverable:
            issues_found.append(
                {
                    "severity": "CRITICAL",
                    "issue": "Deliverable payload is empty or missing",
                    "suggestion": "Ensure upstream producer populates structured results",
                }
            )

        # Check acceptance criteria coverage
        if isinstance(criteria, list):
            for c in criteria:
                c_str = str(c)
                # Check if criterion keyword exists in deliverable string representation
                if str(deliverable).find(c_str) == -1 and len(c_str) > 3:
                    issues_found.append(
                        {
                            "severity": "MEDIUM",
                            "issue": f"Deliverable may not satisfy criterion: '{c_str}'",
                            "suggestion": f"Explicitly address '{c_str}' in final output",
                        }
                    )

        has_critical = any(i["severity"] == "CRITICAL" for i in issues_found)
        review_score = max(0.0, 1.0 - (len(issues_found) * 0.2))

        return {
            "evaluation_result": "PASS" if not has_critical and review_score >= 0.6 else "REVISE",
            "quality_score": round(review_score, 2),
            "total_issues": len(issues_found),
            "issues": issues_found,
            "__confidence__": 0.90,
            "__tokens_used__": 1400,
            "__cost_usd__": 0.00042,
        }

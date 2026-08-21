"""Agent-X Recovery Agent."""

from typing import Any

from agentx.runtime.base import BaseAgent
from agentx.runtime.schemas import AgentInvocationContext, AgentType


class RecoveryAgent(BaseAgent):
    """Specialized agent for diagnosing errors, root cause analysis, and self-healing action formulation."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            agent_type=AgentType.RECOVERY,
            name="RecoveryAgent",
            description="Diagnoses task execution failures and synthesizes self-healing repair actions.",
            capabilities=["recovery"],
            **kwargs,
        )

    async def _execute_internal(self, context: AgentInvocationContext) -> dict[str, Any]:
        """Analyzes failure diagnostics and synthesizes recovery actions."""
        error_msg = str(context.inputs.get("error_message", "Unknown execution failure"))
        retry_count = int(context.inputs.get("retry_count", 0))
        max_retries = int(context.inputs.get("max_retries", 3))

        # Classify error category
        error_lower = error_msg.lower()
        if "429" in error_lower or "resource_exhausted" in error_lower or "quota" in error_lower:
            category = "RATE_LIMIT"
            recommended_action = "BACKOFF_AND_RETRY"
            backoff_seconds = 2.0 ** (retry_count + 1)
        elif "timeout" in error_lower:
            category = "TIMEOUT"
            recommended_action = "INCREASE_TIMEOUT_AND_RETRY"
            backoff_seconds = 1.0
        elif "syntax" in error_lower or "validation" in error_lower or "schema" in error_lower:
            category = "SCHEMA_VALIDATION"
            recommended_action = "REPAIR_PAYLOAD"
            backoff_seconds = 0.0
        elif "auth" in error_lower or "permission" in error_lower:
            category = "AUTHENTICATION_PERMISSION"
            recommended_action = "ESCALATE_HITL"
            backoff_seconds = 0.0
        else:
            category = "TRANSIENT_ERROR"
            recommended_action = "RETRY" if retry_count < max_retries else "ESCALATE_HITL"
            backoff_seconds = 1.0

        can_auto_recover = retry_count < max_retries and category != "AUTHENTICATION_PERMISSION"

        return {
            "error_category": category,
            "root_cause_summary": f"Detected {category} based on: '{error_msg[:80]}'",
            "can_auto_recover": can_auto_recover,
            "recommended_action": recommended_action,
            "backoff_seconds": backoff_seconds,
            "retry_attempt": retry_count + 1,
            "__confidence__": 0.95,
            "__tokens_used__": 1600,
            "__cost_usd__": 0.00048,
        }

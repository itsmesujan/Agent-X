"""Agent-X Dynamic Model Router and Complexity Estimator."""

from agentx.kernel.models import Task
from agentx.resource_brain.pricing import calculate_llm_cost
from agentx.resource_brain.schemas import (
    ModelTier,
    ResourcePrediction,
    TaskComplexityEstimate,
)
from agentx_common.schemas import AgentRole


class ModelRouter:
    """Calculates task complexity and dynamically routes tasks to the optimal Gemini model tier."""

    @staticmethod
    def assess_complexity(
        task: Task,
        reasoning_depth: float = 0.5,
        code_size: float = 0.3,
        tool_count: int = 1,
        is_exploratory: bool = False,
        requires_deep_reasoning: bool = False,
    ) -> TaskComplexityEstimate:
        """Calculate quantitative task complexity score C in [0.0, 1.0]."""
        # Heuristics based on role and inputs if defaults passed
        if task.agent_role in (AgentRole.ARCHITECT, AgentRole.COORDINATOR):
            requires_deep_reasoning = True
            reasoning_depth = max(reasoning_depth, 0.8)
        elif task.agent_role == AgentRole.CODER:
            code_size = max(code_size, 0.6)
            reasoning_depth = max(reasoning_depth, 0.6)
        elif task.agent_role in (AgentRole.AUDITOR, AgentRole.TESTER) and is_exploratory:
            reasoning_depth = min(reasoning_depth, 0.3)

        raw_c = 0.50 * reasoning_depth + 0.30 * code_size + 0.20 * min(1.0, tool_count / 5.0)
        c_score = round(min(1.0, max(0.0, raw_c)), 2)

        return TaskComplexityEstimate(
            task_id=task.task_id,
            reasoning_depth=reasoning_depth,
            code_size=code_size,
            tool_count=tool_count,
            is_exploratory=is_exploratory,
            requires_deep_reasoning=requires_deep_reasoning,
            complexity_score=c_score,
        )

    @classmethod
    def predict_and_route(
        cls,
        task: Task,
        reasoning_depth: float = 0.5,
        code_size: float = 0.3,
        tool_count: int = 1,
        is_exploratory: bool = False,
        requires_deep_reasoning: bool = False,
    ) -> ResourcePrediction:
        """Route task to Gemini 2.5 Flash or Pro and predict token and dollar cost."""
        complexity = cls.assess_complexity(
            task=task,
            reasoning_depth=reasoning_depth,
            code_size=code_size,
            tool_count=tool_count,
            is_exploratory=is_exploratory,
            requires_deep_reasoning=requires_deep_reasoning,
        )

        c = complexity.complexity_score
        if c < 0.40 and not complexity.requires_deep_reasoning:
            selected_model = ModelTier.GEMINI_2_5_FLASH
            pred_input = 4_000
            pred_output = 2_000
            pred_total = 6_000
            pred_duration = min(task.timeout_seconds, 60)
            explanation = (
                f"Routed to Gemini 2.5 Flash: Low task complexity (score: {c:.2f} < 0.40). "
                f"Minimal reasoning depth ({complexity.reasoning_depth:.2f}) enables high throughput and cost savings."
            )
        else:
            selected_model = ModelTier.GEMINI_2_5_PRO
            pred_input = 15_000
            pred_output = 5_000
            pred_total = 20_000
            pred_duration = min(task.timeout_seconds, 300)
            reason_triggers: list[str] = []
            if c >= 0.40:
                reason_triggers.append(f"complexity score {c:.2f} >= 0.40")
            if complexity.requires_deep_reasoning:
                reason_triggers.append("deep reasoning required")

            explanation = (
                f"Routed to Gemini 2.5 Pro: High complexity ({', '.join(reason_triggers)}). "
                f"Assigned for high semantic fidelity and reasoning depth."
            )

        pred_cost = calculate_llm_cost(
            model=selected_model,
            input_tokens=pred_input,
            output_tokens=pred_output,
        )

        return ResourcePrediction(
            task_id=task.task_id,
            predicted_model=selected_model,
            predicted_input_tokens=pred_input,
            predicted_output_tokens=pred_output,
            predicted_total_tokens=pred_total,
            predicted_cost_usd=pred_cost,
            predicted_duration_seconds=pred_duration,
            complexity_score=c,
            explanation=explanation,
        )

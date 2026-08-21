"""Agent-X Data Analysis Tool."""

import math
from typing import Any

from agentx.tools.base import BaseTool
from agentx.tools.schemas import ToolDeclaration, ToolInvocationContext, ToolRiskLevel


class DataAnalysisTool(BaseTool):
    """Tool for quantitative data analysis, aggregation, and statistical metric evaluation."""

    def __init__(self) -> None:
        super().__init__(
            declaration=ToolDeclaration(
                name="data_analysis",
                description="Performs quantitative calculations, statistical summaries, and correlations.",
                capabilities=["analysis"],
                permissions=["compute:eval"],
                risk=ToolRiskLevel.LOW,
                estimated_cost=0.0003,
                timeout=10.0,
                input_schema={
                    "type": "object",
                    "properties": {
                        "numbers": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "List of numeric data points",
                        },
                        "detect_outliers": {"type": "boolean", "default": True},
                    },
                    "required": ["numbers"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "sum": {"type": "number"},
                        "mean": {"type": "number"},
                        "median": {"type": "number"},
                        "std_dev": {"type": "number"},
                        "outliers": {"type": "array"},
                    },
                },
            )
        )

    async def _run(
        self, parameters: dict[str, Any], context: ToolInvocationContext
    ) -> dict[str, Any]:
        raw_nums = parameters.get("numbers")
        if not isinstance(raw_nums, list) or not raw_nums:
            raise ValueError("'numbers' parameter must be a non-empty list of numeric values")

        numbers: list[float] = [float(x) for x in raw_nums]
        n = len(numbers)
        total = sum(numbers)
        mean = total / n

        # Median
        sorted_nums = sorted(numbers)
        if n % 2 == 1:
            median = sorted_nums[n // 2]
        else:
            median = (sorted_nums[n // 2 - 1] + sorted_nums[n // 2]) / 2.0

        # Variance & Std Dev
        variance = sum((x - mean) ** 2 for x in numbers) / n
        std_dev = math.sqrt(variance)

        # Simple 2-sigma Outlier Detection
        outliers: list[float] = []
        if parameters.get("detect_outliers", True) and std_dev > 0:
            outliers = [x for x in numbers if abs(x - mean) > 2.0 * std_dev]

        return {
            "count": n,
            "min": min(numbers),
            "max": max(numbers),
            "sum": round(total, 4),
            "mean": round(mean, 4),
            "median": round(median, 4),
            "variance": round(variance, 4),
            "std_dev": round(std_dev, 4),
            "outliers": outliers,
        }

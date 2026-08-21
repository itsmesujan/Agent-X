"""Agent-X Planner Agent."""

import hashlib
import json
from typing import Any

from agentx.runtime.base import BaseAgent
from agentx.runtime.schemas import AgentInvocationContext, AgentType


class PlannerAgent(BaseAgent):
    """Specialized agent for mission deconstruction, task synthesis, and DAG planning."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            agent_type=AgentType.PLANNER,
            name="PlannerAgent",
            description="Deconstructs high-level objectives into executable DAG tasks and balances constraints.",
            capabilities=["planning"],
            **kwargs,
        )

    async def _execute_internal(self, context: AgentInvocationContext) -> dict[str, Any]:
        """Deconstructs objective into a structured execution plan."""
        objective = context.objective
        inputs = context.inputs

        # Identify major sub-goals
        target_tasks: list[dict[str, Any]] = []
        raw_tasks = inputs.get("tasks")

        if isinstance(raw_tasks, list) and raw_tasks:
            for idx, item in enumerate(raw_tasks):
                t_name = item.get("name", f"Task {idx + 1}")
                t_role = item.get("agent_role", "CODER")
                t_deps = item.get("dependencies", [])
                target_tasks.append(
                    {
                        "task_id": f"task_{idx + 1:03d}",
                        "name": t_name,
                        "agent_role": t_role,
                        "dependencies": t_deps,
                        "estimated_tokens": 15000,
                    }
                )
        else:
            # Algorithmic deconstruction of standard 4-stage pipeline
            target_tasks = [
                {
                    "task_id": "task_001",
                    "name": f"Research Requirements for: {objective[:40]}",
                    "agent_role": "RESEARCHER",
                    "dependencies": [],
                    "estimated_tokens": 10000,
                },
                {
                    "task_id": "task_002",
                    "name": f"Architect and Implement Solution for: {objective[:40]}",
                    "agent_role": "CODER",
                    "dependencies": ["task_001"],
                    "estimated_tokens": 30000,
                },
                {
                    "task_id": "task_003",
                    "name": "Verify Artifacts and Invariants",
                    "agent_role": "VERIFIER",
                    "dependencies": ["task_002"],
                    "estimated_tokens": 8000,
                },
                {
                    "task_id": "task_004",
                    "name": "Compile Final Mission Deliverables",
                    "agent_role": "ARTIFACT",
                    "dependencies": ["task_003"],
                    "estimated_tokens": 5000,
                },
            ]

        plan_hash = hashlib.sha256(
            json.dumps(target_tasks, sort_keys=True).encode("utf-8")
        ).hexdigest()

        return {
            "objective": objective,
            "tasks": target_tasks,
            "total_tasks": len(target_tasks),
            "estimated_duration_seconds": len(target_tasks) * 60,
            "plan_hash": plan_hash,
            "strategy_type": inputs.get("strategy_type", "BALANCED"),
            "__confidence__": 0.95,
            "__tokens_used__": 2500,
            "__cost_usd__": 0.00075,
        }

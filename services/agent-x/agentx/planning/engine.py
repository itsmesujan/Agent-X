"""Agent-X Strategy and Planning Engine Service."""

import json
from uuid import uuid4

from pydantic import BaseModel, Field

from agentx.kernel.models import Task
from agentx.kernel.workflow import CyclicDependencyError, Workflow
from agentx.llm.base import LLMProvider
from agentx.planning.prompts import (
    PLANNING_SYSTEM_INSTRUCTION,
    PLANNING_USER_PROMPT_TEMPLATE,
)
from agentx.planning.schemas import (
    CandidateStrategy,
    PlanningContext,
    StrategyDraftDTO,
    StrategySelectionCriteria,
    StrategySelectionResult,
)
from agentx.planning.selector import StrategySelector
from agentx_common.schemas import TaskStatus


class CandidateStrategiesLLMResponse(BaseModel):
    """Container for LLM structured candidate strategy generation."""

    strategies: list[StrategyDraftDTO] = Field(
        ..., min_length=1, description="List of candidate execution strategies"
    )


class InvalidStrategyError(Exception):
    """Raised when a candidate strategy fails topological or DAG validation."""

    pass


class PlanningEngine:
    """Synthesizes candidate execution strategies and selects optimal workflows dynamically."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        selector: StrategySelector | None = None,
    ) -> None:
        self.llm_provider = llm_provider
        self.selector = selector or StrategySelector()

    def _convert_draft_to_candidate_strategy(
        self,
        draft: StrategyDraftDTO,
        mission_id: str,
    ) -> CandidateStrategy:
        """Validate DAG topology and convert draft DTO into fully instantiated CandidateStrategy."""
        task_ids = {t.task_id for t in draft.tasks}
        dependencies: dict[str, list[str]] = {}
        instantiated_tasks: list[Task] = []

        # 1. Validate dependencies exist within strategy
        for t_draft in draft.tasks:
            for dep in t_draft.dependencies:
                if dep not in task_ids:
                    raise InvalidStrategyError(
                        f"Task '{t_draft.task_id}' has unknown prerequisite dependency '{dep}'"
                    )
            dependencies[t_draft.task_id] = list(t_draft.dependencies)

            task = Task(
                task_id=t_draft.task_id,
                mission_id=mission_id,
                name=t_draft.name,
                description=t_draft.description,
                agent_role=t_draft.agent_role,
                status=TaskStatus.PENDING,
                dependencies=list(t_draft.dependencies),
                expected_outputs=list(t_draft.expected_outputs),
                timeout_seconds=t_draft.timeout_seconds,
                allocated_tokens=t_draft.allocated_tokens,
                verification_level=t_draft.verification_level,
                inputs={
                    "strategy_id": draft.strategy_id,
                    "strategy_type": draft.strategy_type.value,
                },
            )
            instantiated_tasks.append(task)

        # 2. Validate DAG Acyclicity via Workflow topological sort
        try:
            workflow = Workflow(mission_id=mission_id, tasks=instantiated_tasks)
            workflow.validate_dag()
        except CyclicDependencyError as e:
            raise InvalidStrategyError(
                f"Candidate strategy '{draft.name}' contains cyclic dependencies: {e}"
            ) from e
        except Exception as e:
            raise InvalidStrategyError(
                f"Candidate strategy '{draft.name}' failed DAG validation: {e}"
            ) from e

        return CandidateStrategy(
            strategy_id=draft.strategy_id or f"strat_{uuid4().hex[:8]}",
            strategy_type=draft.strategy_type,
            name=draft.name,
            description=draft.description,
            tasks=instantiated_tasks,
            dependencies=dependencies,
            estimated_cost_usd=draft.estimated_cost_usd,
            estimated_tokens=draft.estimated_tokens,
            estimated_duration_seconds=draft.estimated_duration_seconds,
            risk=draft.risk,
            risk_score=draft.risk_score,
            expected_success_probability=draft.expected_success_probability,
            required_capabilities=draft.required_capabilities,
            tradeoffs=draft.tradeoffs,
        )

    def generate_candidate_strategies(
        self,
        context: PlanningContext,
    ) -> list[CandidateStrategy]:
        """Synthesize candidate execution strategies dynamically from mission context."""
        entities_summary = (
            ", ".join(f"{e.entity_type}:{e.name}" for e in context.entities) or "None recorded"
        )
        unknowns_summary = (
            ", ".join(
                f"{u.unknown_id}: {u.question}" for u in context.unknowns if not u.is_resolved
            )
            or "No unresolved unknowns"
        )
        constraints_summary = (
            ", ".join(f"{c.name} ({c.rule_statement})" for c in context.constraints)
            or "Standard boundaries"
        )
        risks_summary = (
            ", ".join(
                f"{r.title} [{r.severity.value}]" for r in context.risks if not r.is_mitigated
            )
            or "No critical risks identified"
        )

        criteria_json = json.dumps([c.model_dump() for c in context.success_criteria], indent=2)

        prompt = PLANNING_USER_PROMPT_TEMPLATE.format(
            goal_statement=context.goal.goal_statement,
            primary_objective=context.goal.primary_objective,
            deliverables=", ".join(context.goal.deliverables),
            success_criteria_json=criteria_json,
            entities_summary=entities_summary,
            unknowns_summary=unknowns_summary,
            constraints_summary=constraints_summary,
            risks_summary=risks_summary,
            max_usd_budget=context.budget.max_usd_limit,
            deadline_seconds=context.deadline_seconds,
            deadline_minutes=context.deadline_seconds / 60.0,
            max_tokens=context.budget.max_total_tokens,
            available_agents=[a.value for a in context.available_agents],
            available_tools=context.available_tools,
        )

        llm_response: CandidateStrategiesLLMResponse = self.llm_provider.generate_structured(
            prompt=prompt,
            response_schema=CandidateStrategiesLLMResponse,
            system_instruction=PLANNING_SYSTEM_INSTRUCTION,
            temperature=0.2,
        )

        candidates: list[CandidateStrategy] = []
        for draft in llm_response.strategies:
            candidate = self._convert_draft_to_candidate_strategy(draft, context.mission_id)
            candidates.append(candidate)

        return candidates

    def plan_and_select_strategy(
        self,
        context: PlanningContext,
        criteria: StrategySelectionCriteria | None = None,
    ) -> StrategySelectionResult:
        """Generate candidate strategies and select the optimal strategy."""
        candidates = self.generate_candidate_strategies(context)
        return self.selector.select_strategy(candidates, context, criteria)

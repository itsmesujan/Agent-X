"""Agent-X Goal Engine Service."""

import json
from uuid import uuid4

from agentx.goal_engine.prompts import (
    GOAL_DECONSTRUCTION_SYSTEM_INSTRUCTION,
    GOAL_DECONSTRUCTION_USER_PROMPT_TEMPLATE,
)
from agentx.goal_engine.schemas import (
    GoalInputOverrides,
    MalformedMissionError,
    ParsedGoalOutput,
)
from agentx.kernel.models import Goal, Mission, MissionState, SuccessCriteria
from agentx.llm.base import LLMProvider
from agentx_common.schemas import MissionStatus, VerificationLevel


class GoalEngine:
    """Deconstructs natural language mission requests into structured, verifiable goal contracts."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider

    def _validate_raw_prompt(self, raw_prompt: str) -> str:
        cleaned = raw_prompt.strip()
        if not cleaned:
            raise MalformedMissionError("Mission prompt cannot be empty or whitespace only")

        if len(cleaned) < 10:
            raise MalformedMissionError(
                f"Mission prompt is too short ({len(cleaned)} characters). Minimum 10 characters required."
            )
        return cleaned

    def _apply_overrides(self, parsed: ParsedGoalOutput, overrides: GoalInputOverrides) -> None:
        if overrides.max_usd_budget is not None:
            parsed.budget.max_usd_limit = overrides.max_usd_budget

        if overrides.max_runtime_minutes is not None:
            parsed.deadline_seconds = overrides.max_runtime_minutes * 60
            parsed.budget.max_execution_time_seconds = parsed.deadline_seconds

        if overrides.initial_constraints:
            parsed.constraints.update(overrides.initial_constraints)

        if overrides.required_deliverables:
            for item in overrides.required_deliverables:
                if item not in parsed.deliverables:
                    parsed.deliverables.append(item)

    def _post_validate(self, parsed: ParsedGoalOutput) -> None:
        if not parsed.success_criteria:
            parsed.success_criteria.append(
                SuccessCriteria(
                    description=f"Verify completion of primary objective: {parsed.primary_objective}",
                    verification_level=VerificationLevel.LEVEL_4_SEMANTIC,
                )
            )

        if not parsed.deliverables:
            parsed.deliverables = ["verified_mission_outcome"]

    def deconstruct_goal(
        self,
        raw_prompt: str,
        overrides: GoalInputOverrides | None = None,
    ) -> ParsedGoalOutput:
        """Parse and validate a natural language prompt into a structured ParsedGoalOutput."""
        cleaned_prompt = self._validate_raw_prompt(raw_prompt)
        overrides_obj = overrides or GoalInputOverrides()
        overrides_json = json.dumps(overrides_obj.model_dump(exclude_none=True), indent=2)

        prompt = GOAL_DECONSTRUCTION_USER_PROMPT_TEMPLATE.format(
            user_prompt=cleaned_prompt,
            overrides_json=overrides_json,
        )

        parsed: ParsedGoalOutput = self.llm_provider.generate_structured(
            prompt=prompt,
            response_schema=ParsedGoalOutput,
            system_instruction=GOAL_DECONSTRUCTION_SYSTEM_INSTRUCTION,
            temperature=0.1,
        )

        self._apply_overrides(parsed, overrides_obj)
        self._post_validate(parsed)
        return parsed

    def create_mission_from_goal(
        self,
        parsed_goal: ParsedGoalOutput,
        mission_id: str | None = None,
    ) -> Mission:
        """Convert a ParsedGoalOutput into a Kernel Mission domain entity."""
        kernel_goal = Goal(
            goal_statement=parsed_goal.goal_statement,
            primary_objective=parsed_goal.primary_objective,
            deliverables=parsed_goal.deliverables,
            constraints=parsed_goal.constraints,
            success_criteria=parsed_goal.success_criteria,
        )

        mission = Mission(
            mission_id=mission_id or f"msn_{uuid4().hex[:12]}",
            title=parsed_goal.title,
            goal=kernel_goal,
            state=MissionState(status=MissionStatus.DRAFT),
            budget=parsed_goal.budget,
            metadata={
                "risk_level": parsed_goal.risk_level.value,
                "risk_summary": parsed_goal.risk_summary,
                "required_capabilities": [c.value for c in parsed_goal.required_capabilities],
                "deadline_seconds": parsed_goal.deadline_seconds,
            },
        )
        return mission

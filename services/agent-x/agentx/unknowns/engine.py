"""Agent-X Unknowns Engine Service."""

from collections import defaultdict
from typing import Any

from agentx.kernel.models import Task
from agentx.unknowns.calculator import (
    TASK_CONVERSION_THRESHOLD,
    evaluate_unknown_priority,
)
from agentx.unknowns.schemas import (
    ConflictReport,
    EpistemicUnknown,
    PrioritizedUnknown,
)
from agentx.world_model.models import Fact
from agentx_common.schemas import AgentRole, EpistemicState, TaskStatus, VerificationLevel


class UnknownsEngine:
    """Discovers, scores, manages, and translates epistemic unknowns into exploration tasks."""

    def __init__(self, conversion_threshold: float = TASK_CONVERSION_THRESHOLD) -> None:
        self.conversion_threshold = conversion_threshold

    def assess_unknown(
        self,
        unknown: EpistemicUnknown,
        deadline_remaining_ratio: float | None = None,
    ) -> PrioritizedUnknown:
        """Evaluate an unknown and generate its explainable priority breakdown."""
        breakdown = evaluate_unknown_priority(
            unknown=unknown,
            deadline_remaining_ratio=deadline_remaining_ratio,
            conversion_threshold=self.conversion_threshold,
        )
        return PrioritizedUnknown(unknown=unknown, evaluation=breakdown)

    def rank_unknowns(
        self,
        unknowns: list[EpistemicUnknown],
        deadline_remaining_ratio: float | None = None,
    ) -> list[PrioritizedUnknown]:
        """Assess and sort unknowns in descending order of priority score."""
        evaluated = [
            self.assess_unknown(unk, deadline_remaining_ratio=deadline_remaining_ratio)
            for unk in unknowns
        ]
        return sorted(evaluated, key=lambda item: item.evaluation.priority_score, reverse=True)

    def detect_conflicts(self, mission_id: str, facts: list[Fact]) -> list[ConflictReport]:
        """Detect conflicting claims or values across valid facts and synthesize investigation unknowns."""
        # Group valid facts by (subject.lower(), predicate.lower())
        grouped_facts: dict[tuple[str, str], list[Fact]] = defaultdict(list)
        for fact in facts:
            if fact.is_valid and fact.mission_id == mission_id:
                key = (fact.subject.strip().lower(), fact.predicate.strip().lower())
                grouped_facts[key].append(fact)

        reports: list[ConflictReport] = []
        for (subject, predicate), fact_list in grouped_facts.items():
            if len(fact_list) < 2:
                continue

            # Compare distinct values
            distinct_values: list[Any] = []
            distinct_facts: list[Fact] = []
            for f in fact_list:
                if f.value not in distinct_values:
                    distinct_values.append(f.value)
                    distinct_facts.append(f)

            if len(distinct_values) > 1:
                # Conflicting evidence detected!
                entity_id = distinct_facts[0].entity_id
                val_repr = ", ".join(str(v) for v in distinct_values)
                question = (
                    f"Conflict detected for '{subject}' property '{predicate}': "
                    f"Conflicting values [{val_repr}]. Which value is currently true in the environment?"
                )

                conflict_unknown = EpistemicUnknown(
                    mission_id=mission_id,
                    target_entity_id=entity_id,
                    question=question,
                    impact_description=f"Direct contradictory evidence for {subject}.{predicate} threatens downstream correctness.",
                    impact=0.90,
                    uncertainty=1.0,
                    decision_relevance=0.85,
                    research_cost=0.15,
                    urgency=0.80,
                    suggested_agent_role=AgentRole.AUDITOR,
                    discovery_strategy="VERIFY_CONTRADICTORY_EVIDENCE",
                    epistemic_state=EpistemicState.CRITICAL_UNKNOWN,
                    metadata={"conflicting_fact_ids": [f.fact_id for f in distinct_facts]},
                )

                reports.append(
                    ConflictReport(
                        mission_id=mission_id,
                        entity_id=entity_id,
                        subject=subject,
                        predicate=predicate,
                        conflicting_fact_ids=[f.fact_id for f in distinct_facts],
                        conflicting_values=distinct_values,
                        detected_unknown=conflict_unknown,
                    )
                )

        return reports

    def convert_unknown_to_task(
        self,
        prioritized: PrioritizedUnknown,
        mission_id: str,
        assigned_role: AgentRole | None = None,
    ) -> Task:
        """Convert a high-priority unknown into an executable, read-only exploration task."""
        unk = prioritized.unknown
        role = assigned_role or unk.suggested_agent_role
        task_id = f"task_explore_{unk.unknown_id}"

        task = Task(
            task_id=task_id,
            mission_id=mission_id,
            name=f"Explore Unknown: {unk.question[:80]}",
            description=(
                f"Exploratory discovery task to resolve epistemic unknown '{unk.unknown_id}'.\n"
                f"Question: {unk.question}\n"
                f"Impact: {unk.impact_description}\n"
                f"Strategy: {unk.discovery_strategy}\n"
                f"Priority Rationale: {prioritized.evaluation.explanation}"
            ),
            agent_role=role,
            status=TaskStatus.PENDING,
            inputs={
                "unknown_id": unk.unknown_id,
                "question": unk.question,
                "target_entity_id": unk.target_entity_id,
                "discovery_strategy": unk.discovery_strategy,
                "discovery_command": unk.discovery_command,
                "is_exploratory": True,
                "priority_tier": prioritized.evaluation.tier.value,
                "priority_score": prioritized.evaluation.priority_score,
            },
            verification_level=VerificationLevel.LEVEL_2_EXECUTION,
            timeout_seconds=300,
        )
        return task

    def convert_eligible_unknowns(
        self,
        unknowns: list[EpistemicUnknown],
        mission_id: str,
        deadline_remaining_ratio: float | None = None,
    ) -> list[tuple[PrioritizedUnknown, Task]]:
        """Filter unknowns that meet conversion thresholds and synthesize corresponding exploration tasks."""
        ranked = self.rank_unknowns(unknowns, deadline_remaining_ratio=deadline_remaining_ratio)
        results: list[tuple[PrioritizedUnknown, Task]] = []

        for p_unk in ranked:
            if p_unk.evaluation.should_convert_to_task and not p_unk.unknown.is_resolved:
                task = self.convert_unknown_to_task(p_unk, mission_id=mission_id)
                results.append((p_unk, task))

        return results

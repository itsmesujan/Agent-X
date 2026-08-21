"""Agent-X Relevance Evaluator for Computing Goal Alignment Scores."""

import re

from agentx.drift.schemas import DriftSeverity, TaskRelevanceReport
from agentx.kernel.models import Mission, Task

STOPWORDS: set[str] = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "is",
    "are",
    "was",
    "be",
    "this",
    "that",
    "as",
    "it",
    "from",
}


def tokenize(text: str) -> set[str]:
    """Extract normalized lowercase alphanumeric keywords excluding stopwords."""
    words = re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text.lower())
    return {w for w in words if w not in STOPWORDS}


class RelevanceEvaluator:
    """Computes semantic similarity and deliverable contribution between tasks and mission goals."""

    def __init__(
        self,
        drift_threshold: float = 0.60,
        critical_threshold: float = 0.20,
    ) -> None:
        self.drift_threshold = drift_threshold
        self.critical_threshold = critical_threshold

    def evaluate_task(self, task: Task, mission: Mission) -> TaskRelevanceReport:
        """Evaluates whether an active task remains aligned with the core mission objective."""
        # 1. Mission Intent Keywords
        mission_text = (
            f"{mission.title} {mission.goal.goal_statement} "
            f"{mission.goal.primary_objective} {' '.join(mission.goal.deliverables)}"
        )
        mission_tokens = tokenize(mission_text)

        # 2. Task Intent Keywords
        task_text = f"{task.name} {task.description} {' '.join(task.expected_outputs)}"
        task_tokens = tokenize(task_text)
        name_tokens = tokenize(task.name)

        # 3. Calculate Semantic Similarity
        if not task_tokens or not mission_tokens:
            semantic_sim = 0.5
        else:
            intersection = task_tokens.intersection(mission_tokens)
            containment = len(intersection) / len(task_tokens)

            # Name focus alignment
            name_intersection = name_tokens.intersection(mission_tokens)
            name_containment = len(name_intersection) / len(name_tokens) if name_tokens else 0.0

            semantic_sim = min(1.0, max(0.0, 0.60 * containment + 0.40 * name_containment))

        # 4. Deliverable Contribution
        mission_delivs = {d.lower() for d in mission.goal.deliverables}
        task_outputs = {o.lower() for o in task.expected_outputs}

        if task_outputs and any(
            any(d_kw in out for d_kw in tokenize(deliv))
            for out in task_outputs
            for deliv in mission_delivs
        ):
            deliv_score = 0.95
        elif any(deliv in task_text.lower() for deliv in mission_delivs):
            deliv_score = 0.85
        elif not task.expected_outputs:
            deliv_score = 0.60
        elif task_tokens.intersection(mission_tokens):
            # Partial topic overlap
            deliv_score = 0.40
        else:
            deliv_score = 0.05

        # 5. Composite Relevance Score
        composite_score = round(0.50 * semantic_sim + 0.50 * deliv_score, 4)

        # 6. Severity Classification
        if composite_score >= self.drift_threshold:
            severity = DriftSeverity.ALIGNED
            explanation = f"Task '{task.name}' is strongly aligned with mission goal (score: {composite_score:.2f})."
        elif composite_score >= self.critical_threshold:
            severity = DriftSeverity.MODERATE_DRIFT
            explanation = (
                f"Task '{task.name}' exhibits moderate goal drift (score: {composite_score:.2f} < {self.drift_threshold:.2f}). "
                "Task appears tangential to core mission deliverables."
            )
        else:
            severity = DriftSeverity.CRITICAL_DRIFT
            explanation = (
                f"Task '{task.name}' exhibits CRITICAL goal drift (score: {composite_score:.2f} < {self.critical_threshold:.2f}). "
                "Task is completely out-of-scope or disjoint from mission objective."
            )

        return TaskRelevanceReport(
            task_id=task.task_id,
            mission_id=mission.mission_id,
            relevance_score=composite_score,
            semantic_similarity=round(semantic_sim, 4),
            deliverable_contribution=round(deliv_score, 4),
            severity=severity,
            explanation=explanation,
        )

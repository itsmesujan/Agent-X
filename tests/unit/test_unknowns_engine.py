"""Unit tests for Agent-X Unknowns Engine."""

from agentx.unknowns import (
    EpistemicUnknown,
    PriorityTier,
    UnknownsEngine,
    evaluate_unknown_priority,
)
from agentx.world_model.models import Fact, SourceProvenance, SourceType
from agentx_common.schemas import AgentRole


def test_high_impact_unknown_priority() -> None:
    """Test high-impact, high-relevance unknown calculation and task conversion recommendation."""
    engine = UnknownsEngine()

    unknown = EpistemicUnknown(
        mission_id="msn_unk_01",
        question="What is the production database connection string?",
        impact_description="Without connection string, backend migration task will fail entirely.",
        impact=0.95,
        decision_relevance=0.90,
        uncertainty=0.95,
        research_cost=0.10,
        urgency=0.80,
        blocking_task_ids=["task_db_migrate_01", "task_db_migrate_02"],
        suggested_agent_role=AgentRole.DEVOPS,
    )

    prioritized = engine.assess_unknown(unknown)
    evaluation = prioritized.evaluation

    assert evaluation.priority_score >= 80.0
    assert evaluation.tier == PriorityTier.CRITICAL
    assert evaluation.should_convert_to_task is True
    assert "high failure impact" in evaluation.explanation
    assert "blocking 2 downstream task(s)" in evaluation.explanation

    # Verify task synthesis
    task = engine.convert_unknown_to_task(prioritized, mission_id="msn_unk_01")
    assert task.mission_id == "msn_unk_01"
    assert task.agent_role == AgentRole.DEVOPS
    assert task.inputs["priority_score"] >= 80.0
    assert task.inputs["unknown_id"] == unknown.unknown_id
    assert task.idempotency_key != ""


def test_low_impact_unknown_priority() -> None:
    """Test low-impact, low-relevance unknown does not exceed threshold for task conversion."""
    engine = UnknownsEngine()

    unknown = EpistemicUnknown(
        mission_id="msn_unk_01",
        question="What is the exact color hex code of the footer border in the styleguide?",
        impact_description="Minor aesthetic detail, default fallback style is acceptable.",
        impact=0.15,
        decision_relevance=0.10,
        uncertainty=0.40,
        research_cost=0.60,
        urgency=0.10,
        suggested_agent_role=AgentRole.CODER,
    )

    prioritized = engine.assess_unknown(unknown)
    evaluation = prioritized.evaluation

    assert evaluation.priority_score < 45.0
    assert evaluation.tier == PriorityTier.LOW
    assert evaluation.should_convert_to_task is False
    assert "low mission impact" in evaluation.explanation


def test_resolved_unknown_priority() -> None:
    """Test that a resolved unknown receives a priority score of 0 and is not converted to tasks."""
    engine = UnknownsEngine()

    unknown = EpistemicUnknown(
        mission_id="msn_unk_01",
        question="Is Docker installed on the runner host?",
        impact_description="Required to build container images.",
        impact=0.90,
        decision_relevance=0.85,
        uncertainty=0.90,
        is_resolved=True,
        resolved_fact_id="fct_docker_installed_true",
    )

    prioritized = engine.assess_unknown(unknown)
    evaluation = prioritized.evaluation

    assert evaluation.priority_score == 0.0
    assert evaluation.tier == PriorityTier.LOW
    assert evaluation.should_convert_to_task is False
    assert "already resolved" in evaluation.explanation

    eligible = engine.convert_eligible_unknowns([unknown], mission_id="msn_unk_01")
    assert len(eligible) == 0


def test_conflicting_evidence_detection() -> None:
    """Test detection of contradictory facts and automatic synthesis of investigation unknown."""
    engine = UnknownsEngine()

    fact1 = Fact(
        fact_id="fct_port_source_a",
        mission_id="msn_unk_01",
        subject="AgentX Backend",
        predicate="port",
        value=3000,
        source=SourceProvenance(source_type=SourceType.FILE_CONTENT, source_ref="package.json"),
    )
    fact2 = Fact(
        fact_id="fct_port_source_b",
        mission_id="msn_unk_01",
        subject="AgentX Backend",
        predicate="port",
        value=8000,
        source=SourceProvenance(source_type=SourceType.FILE_CONTENT, source_ref="Dockerfile"),
    )

    conflict_reports = engine.detect_conflicts("msn_unk_01", [fact1, fact2])

    assert len(conflict_reports) == 1
    report = conflict_reports[0]
    assert report.subject == "agentx backend"
    assert report.predicate == "port"
    assert len(report.conflicting_fact_ids) == 2
    assert set(report.conflicting_values) == {3000, 8000}

    # Verify synthesized unknown is high-priority
    unk = report.detected_unknown
    assert unk.impact == 0.90
    assert unk.suggested_agent_role == AgentRole.AUDITOR

    prioritized = engine.assess_unknown(unk)
    assert prioritized.evaluation.tier in (PriorityTier.CRITICAL, PriorityTier.HIGH)
    assert prioritized.evaluation.should_convert_to_task is True


def test_deadline_pressure_dynamics() -> None:
    """Test that approaching deadlines significantly increase unknown urgency and priority score."""
    unknown = EpistemicUnknown(
        mission_id="msn_unk_01",
        question="Which Cloud Run region should be targeted for deployment?",
        impact_description="Determines latency and IAM permissions.",
        impact=0.60,
        decision_relevance=0.60,
        uncertainty=0.70,
        urgency=0.40,
        research_cost=0.20,
    )

    # 1. Normal state with plenty of time (85% remaining)
    normal_eval = evaluate_unknown_priority(unknown, deadline_remaining_ratio=0.85)

    # 2. Critical time pressure (10% remaining)
    crunch_eval = evaluate_unknown_priority(unknown, deadline_remaining_ratio=0.10)

    assert crunch_eval.priority_score > normal_eval.priority_score
    assert crunch_eval.weighted_urgency > normal_eval.weighted_urgency
    assert "severe deadline pressure" in crunch_eval.explanation


def test_ranking_and_batch_task_conversion() -> None:
    """Test ranking multiple unknowns and converting only eligible ones into tasks."""
    engine = UnknownsEngine()

    unk_high = EpistemicUnknown(
        mission_id="msn_unk_01",
        question="Are Cloud Run service credentials available?",
        impact_description="Crucial for all infra tasks.",
        impact=0.95,
        decision_relevance=0.90,
        uncertainty=0.90,
        urgency=0.80,
    )
    unk_med = EpistemicUnknown(
        mission_id="msn_unk_01",
        question="What is the default log retention period?",
        impact_description="Useful for compliance.",
        impact=0.50,
        decision_relevance=0.45,
        uncertainty=0.50,
        urgency=0.40,
    )
    unk_low = EpistemicUnknown(
        mission_id="msn_unk_01",
        question="Is the README badges URL accessible?",
        impact_description="Cosmetic.",
        impact=0.10,
        decision_relevance=0.10,
        uncertainty=0.20,
        urgency=0.10,
    )

    ranked = engine.rank_unknowns([unk_med, unk_high, unk_low])

    assert ranked[0].unknown.question == unk_high.question
    assert ranked[1].unknown.question == unk_med.question
    assert ranked[2].unknown.question == unk_low.question

    eligible = engine.convert_eligible_unknowns(
        [unk_high, unk_med, unk_low], mission_id="msn_unk_01"
    )
    assert len(eligible) >= 1
    assert eligible[0][0].unknown.question == unk_high.question
    assert eligible[0][1].status.value == "PENDING"

"""Unit tests and Goal Drift Recovery Demonstrations for Agent-X."""

from agentx.drift import (
    DriftRemediationAction,
    DriftSeverity,
    GoalDriftDetector,
    RelevanceEvaluator,
)
from agentx.kernel.events import EventBus, EventType, KernelEvent
from agentx.kernel.models import Goal, Mission, MissionState, Task
from agentx.kernel.workflow import Workflow
from agentx_common.schemas import AgentRole, MissionStatus, TaskStatus


def make_firestore_mission() -> Mission:
    return Mission(
        mission_id="msn_drift_01",
        title="Production Firestore Deployment",
        goal=Goal(
            goal_statement="Deploy multi-region production Firestore database with strict security rules and backup schedules",
            primary_objective="Deploy production Firestore and security rules",
            deliverables=["firestore.rules", "firestore_spec.json", "backup_policy.json"],
        ),
        state=MissionState(status=MissionStatus.EXECUTING),
    )


def test_relevance_evaluator_alignment_and_drift() -> None:
    """Test RelevanceEvaluator correctly distinguishes aligned, tangential, and critically drifted tasks."""
    mission = make_firestore_mission()
    evaluator = RelevanceEvaluator(drift_threshold=0.60, critical_threshold=0.20)

    # 1. Aligned Task
    task_aligned = Task(
        task_id="task_01",
        mission_id=mission.mission_id,
        name="Compile Firestore Security Rules",
        description="Write and validate firestore.rules for production collections",
        agent_role=AgentRole.DEVOPS,
        expected_outputs=["firestore.rules"],
    )
    rep_aligned = evaluator.evaluate_task(task_aligned, mission)
    assert rep_aligned.severity == DriftSeverity.ALIGNED
    assert rep_aligned.relevance_score >= 0.70

    # 2. Moderate Drift (Tangential)
    task_tangential = Task(
        task_id="task_02",
        mission_id=mission.mission_id,
        name="Draft Marketing Blog Post",
        description="Write an introductory blog post explaining database architectures for developer advocacy",
        agent_role=AgentRole.CODER,
        expected_outputs=["blog_post.md"],
    )
    rep_tangential = evaluator.evaluate_task(task_tangential, mission)
    assert rep_tangential.severity == DriftSeverity.MODERATE_DRIFT
    assert 0.20 <= rep_tangential.relevance_score < 0.60

    # 3. Critical Drift (Completely out of scope)
    task_critical = Task(
        task_id="task_03",
        mission_id=mission.mission_id,
        name="Render 3D WebGL Game Graphics",
        description="Build threejs shader pipeline for space shooter video game",
        agent_role=AgentRole.CODER,
        expected_outputs=["game_shaders.glsl"],
    )
    rep_critical = evaluator.evaluate_task(task_critical, mission)
    assert rep_critical.severity == DriftSeverity.CRITICAL_DRIFT
    assert rep_critical.relevance_score < 0.20


def test_workflow_evaluation_and_drift_detection_event() -> None:
    """Test full workflow evaluation and emission of GOAL_DRIFT_DETECTED event."""
    event_bus = EventBus()
    events: list[KernelEvent] = []
    event_bus.subscribe_all(lambda e: events.append(e))

    detector = GoalDriftDetector(event_bus=event_bus)
    mission = make_firestore_mission()
    workflow = Workflow(mission_id=mission.mission_id, event_bus=event_bus)

    # Add 1 aligned task and 1 critically drifted task
    workflow.create_task(
        task_id="task_good",
        name="Configure Firestore Backup Schedule",
        description="Deploy backup policy in GCP",
        agent_role=AgentRole.DEVOPS,
        expected_outputs=["backup_policy.json"],
    )
    workflow.create_task(
        task_id="task_drifted",
        name="Create Crypto Trading Bot Strategy",
        description="Implement automated high frequency arbitrage algorithm",
        agent_role=AgentRole.CODER,
        expected_outputs=["trading_bot.py"],
    )

    eval_result = detector.evaluate_workflow(mission, workflow)

    assert eval_result.drifted_task_count == 1
    assert "task_drifted" in eval_result.recommended_remediations
    assert eval_result.recommended_remediations["task_drifted"] == DriftRemediationAction.CANCEL

    # Verify event published
    assert any(e.event_type == EventType.GOAL_DRIFT_DETECTED for e in events)


def test_goal_drift_remediation_flag_pause_cancel_reprioritize() -> None:
    """Test individual drift remediation actions: FLAG, PAUSE, CANCEL, REPRIORITIZE."""
    event_bus = EventBus()
    detector = GoalDriftDetector(event_bus=event_bus)
    mission = make_firestore_mission()
    workflow = Workflow(mission_id=mission.mission_id, event_bus=event_bus)

    t1 = workflow.create_task(
        task_id="t1", name="Task 1", description="Desc", agent_role=AgentRole.CODER
    )
    t2 = workflow.create_task(
        task_id="t2", name="Task 2", description="Desc", agent_role=AgentRole.CODER
    )
    t3 = workflow.create_task(
        task_id="t3", name="Task 3", description="Desc", agent_role=AgentRole.CODER
    )
    t4 = workflow.create_task(
        task_id="t4", name="Task 4", description="Desc", agent_role=AgentRole.CODER
    )

    # 1. FLAG
    rec_flag = detector.remediate_drift(mission, workflow, "t1", DriftRemediationAction.FLAG)
    assert rec_flag.details["status"] == "FLAGGED"
    assert t1.inputs.get("goal_drift_flagged") is True

    # 2. PAUSE
    rec_pause = detector.remediate_drift(mission, workflow, "t2", DriftRemediationAction.PAUSE)
    assert rec_pause.details["status"] == "PAUSED"
    assert t2.status == TaskStatus.PAUSED

    # 3. CANCEL
    rec_cancel = detector.remediate_drift(mission, workflow, "t3", DriftRemediationAction.CANCEL)
    assert rec_cancel.details["status"] == "SKIPPED"
    assert t3.status == TaskStatus.SKIPPED

    # 4. REPRIORITIZE
    orig_tokens = t4.allocated_tokens
    rec_reprioritize = detector.remediate_drift(
        mission, workflow, "t4", DriftRemediationAction.REPRIORITIZE
    )
    assert rec_reprioritize.details["new_priority"] == 1
    assert t4.allocated_tokens <= orig_tokens // 2


def test_goal_drift_remediation_replace() -> None:
    """Test REPLACE action substituting a drifted task with an aligned task."""
    event_bus = EventBus()
    detector = GoalDriftDetector(event_bus=event_bus)
    mission = make_firestore_mission()
    workflow = Workflow(mission_id=mission.mission_id, event_bus=event_bus)

    # Add prerequisite setup
    workflow.create_task(
        task_id="p1", name="Prereq", description="Prereq", agent_role=AgentRole.DEVOPS
    )

    # Add drifted task dependent on p1
    drifted_task = workflow.create_task(
        task_id="task_drifted_orig",
        name="Unrelated Audio Processing",
        description="Filter mp3 audio waves",
        agent_role=AgentRole.CODER,
        dependencies=["p1"],
    )

    # Substitute with aligned replacement task
    replacement = Task(
        task_id="task_aligned_new",
        mission_id=mission.mission_id,
        name="Deploy Firestore Indexes",
        description="Generate and deploy firestore.indexes.json",
        agent_role=AgentRole.DEVOPS,
        expected_outputs=["firestore.indexes.json"],
    )

    rec_replace = detector.remediate_drift(
        mission=mission,
        workflow=workflow,
        task_id="task_drifted_orig",
        action=DriftRemediationAction.REPLACE,
        replacement_task=replacement,
        reason="Replace audio task with Firestore indexes deployment",
    )

    assert rec_replace.details["status"] == "REPLACED"
    assert drifted_task.status == TaskStatus.SKIPPED
    assert "task_aligned_new" in [t.task_id for t in workflow.get_all_tasks()]
    assert workflow.get_task("task_aligned_new").dependencies == ["p1"]

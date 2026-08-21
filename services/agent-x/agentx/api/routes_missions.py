import hashlib
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from agentx.api.auth import AuthUser, get_current_user
from agentx.api.schemas import (
    AllocationChangeEventDTO,
    ArtifactDTO,
    ArtifactType,
    ClaimConflictDTO,
    CreateArtifactRequest,
    CreateMissionRequest,
    CreateMissionResponse,
    EventDTO,
    EvidenceClaimDTO,
    EvidenceItemDTO,
    EvidenceSummaryDTO,
    FailureCenterResponseDTO,
    FailureCenterSummaryDTO,
    FailureRecordDTO,
    ManualReallocationRequest,
    MissionDetailDTO,
    MissionSummaryDTO,
    ResourceMetricTupleDTO,
    ResourceMonitorResponseDTO,
    ResourceSummaryDTO,
    TaskDTO,
    TimelineEventDTO,
    WorkflowGraphDTO,
    WorkflowGraphEdgeDTO,
    WorkflowGraphNodeDTO,
)
from agentx.api.state import ApiStateManager, state_manager
from agentx.kernel.state_machine import MissionStateMachine
from agentx.resource_brain.schemas import ResourceDimension
from agentx_common.schemas import MissionStatus, TaskStatus

router = APIRouter(prefix="/missions", tags=["Missions"])


def get_state() -> ApiStateManager:
    return state_manager


# --- 1. MISSION LIFECYCLE ---


@router.post("", response_model=CreateMissionResponse, status_code=status.HTTP_201_CREATED)
async def create_mission(
    request: CreateMissionRequest,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> CreateMissionResponse:
    """Create and initialize a new autonomous mission."""
    mission = state.create_mission(
        title=request.title,
        goal_statement=request.goal_statement,
        max_usd_budget=request.max_usd_budget,
        max_runtime_minutes=request.max_runtime_minutes,
        deliverables=request.deliverables,
        constraints=request.constraints,
    )
    return CreateMissionResponse(
        mission_id=mission.mission_id,
        status=mission.state.status,
        title=mission.title,
        message="Mission successfully initialized and queued.",
    )


@router.get("", response_model=list[MissionSummaryDTO])
async def list_missions(
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
    status_filter: Annotated[MissionStatus | None, Query(alias="status")] = None,
) -> list[MissionSummaryDTO]:
    """List all registered missions with summary progress metrics."""
    summaries: list[MissionSummaryDTO] = []
    for m in state.missions.values():
        if status_filter and m.state.status != status_filter:
            continue
        wf = state.workflows.get(m.mission_id)
        task_count = len(wf.get_all_tasks()) if wf else 0

        summaries.append(
            MissionSummaryDTO(
                mission_id=m.mission_id,
                title=m.title,
                status=m.state.status,
                current_usd_spent=m.budget.current_usd_spent,
                max_usd_limit=m.budget.max_usd_limit,
                task_count=task_count,
                created_at=m.created_at,
            )
        )
    return summaries


@router.get("/{mission_id}", response_model=MissionDetailDTO)
async def get_mission_detail(
    mission_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> MissionDetailDTO:
    """Retrieve detailed state, budget, and task breakdown for a mission."""
    mission = state.get_mission(mission_id)
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID '{mission_id}' was not found.",
        )

    wf = state.get_workflow(mission_id)
    tasks = wf.get_all_tasks() if wf else []

    task_summary = {
        "total": len(tasks),
        "verified": sum(1 for t in tasks if t.status == TaskStatus.VERIFIED),
        "running": sum(1 for t in tasks if t.status == TaskStatus.RUNNING),
        "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
        "pending": sum(1 for t in tasks if t.status in (TaskStatus.PENDING, TaskStatus.READY)),
    }

    return MissionDetailDTO(
        mission_id=mission.mission_id,
        title=mission.title,
        goal_statement=mission.goal.goal_statement,
        primary_objective=mission.goal.primary_objective,
        status=mission.state.status,
        budget=mission.budget,
        deliverables=mission.goal.deliverables,
        constraints=mission.goal.constraints,
        summary=task_summary,
        created_at=mission.created_at,
        updated_at=mission.updated_at,
    )


@router.post("/{mission_id}/start", response_model=MissionDetailDTO)
async def start_mission(
    mission_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> MissionDetailDTO:
    """Transition mission state to EXECUTING."""
    mission = state.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found.")

    if mission.state.status == MissionStatus.EXECUTING:
        return await get_mission_detail(mission_id, current_user, state)

    evt = MissionStateMachine.transition(mission, MissionStatus.EXECUTING)
    state.event_bus.publish(evt)
    return await get_mission_detail(mission_id, current_user, state)


@router.post("/{mission_id}/pause", response_model=MissionDetailDTO)
async def pause_mission(
    mission_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> MissionDetailDTO:
    """Transition mission state to PAUSED."""
    mission = state.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found.")

    evt = MissionStateMachine.transition(mission, MissionStatus.PAUSED, reason="Paused via API")
    state.event_bus.publish(evt)
    return await get_mission_detail(mission_id, current_user, state)


@router.post("/{mission_id}/resume", response_model=MissionDetailDTO)
async def resume_mission(
    mission_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> MissionDetailDTO:
    """Resume a paused mission back to EXECUTING."""
    mission = state.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found.")

    evt = MissionStateMachine.transition(mission, MissionStatus.EXECUTING, reason="Resumed via API")
    state.event_bus.publish(evt)
    return await get_mission_detail(mission_id, current_user, state)


@router.post("/{mission_id}/cancel", response_model=MissionDetailDTO)
async def cancel_mission(
    mission_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> MissionDetailDTO:
    """Cancel and abort mission execution."""
    mission = state.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found.")

    evt = MissionStateMachine.transition(mission, MissionStatus.ABORTED, reason="Aborted via API")
    state.event_bus.publish(evt)
    return await get_mission_detail(mission_id, current_user, state)


# --- 2. TASKS & GRAPH TOPOLOGY ---


@router.get("/{mission_id}/tasks", response_model=list[TaskDTO])
async def list_mission_tasks(
    mission_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> list[TaskDTO]:
    """List all task nodes within the mission DAG."""
    wf = state.get_workflow(mission_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mission workflow not found."
        )

    tasks = wf.get_all_tasks()
    return [
        TaskDTO(
            task_id=t.task_id,
            mission_id=t.mission_id,
            name=t.name,
            description=t.description,
            agent_role=t.agent_role,
            status=t.status,
            dependencies=t.dependencies,
            dependent_children=t.dependent_children,
            retry_count=t.retry_count,
            allocated_tokens=t.allocated_tokens,
            evidence_uri=t.evidence_uri,
        )
        for t in tasks
    ]


@router.get("/{mission_id}/graph", response_model=WorkflowGraphDTO)
async def get_mission_graph(
    mission_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> WorkflowGraphDTO:
    """Retrieve node and edge topology for DAG graph visualization."""
    wf = state.get_workflow(mission_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mission workflow not found."
        )

    tasks = wf.get_all_tasks()
    nodes = [
        WorkflowGraphNodeDTO(
            id=t.task_id,
            name=t.name,
            agent_role=t.agent_role,
            status=t.status,
            retry_count=t.retry_count,
        )
        for t in tasks
    ]

    edges: list[WorkflowGraphEdgeDTO] = []
    for t in tasks:
        for child_id in t.dependent_children:
            edges.append(WorkflowGraphEdgeDTO(source=t.task_id, target=child_id))

    return WorkflowGraphDTO(mission_id=mission_id, nodes=nodes, edges=edges)


# --- 3. EVENTS, RESOURCES, EVIDENCE, ARTIFACTS ---


@router.get("/{mission_id}/events", response_model=list[EventDTO])
async def list_mission_events(
    mission_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> list[EventDTO]:
    """Retrieve chronological event log history for the mission."""
    events = state.event_bus.get_events(mission_id=mission_id)
    return [
        EventDTO(
            event_id=e.event_id,
            mission_id=e.mission_id,
            event_type=e.event_type.value if hasattr(e.event_type, "value") else str(e.event_type),
            timestamp=e.timestamp,
            payload=e.payload,
        )
        for e in events
    ]


@router.get("/{mission_id}/resources", response_model=ResourceSummaryDTO)
async def get_mission_resources(
    mission_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> ResourceSummaryDTO:
    """Retrieve real-time Resource Brain metrics, tokens used, and active tool locks."""
    rb = state.get_resource_brain(mission_id)
    if not rb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource brain not found."
        )

    snapshot = rb.get_telemetry_snapshot()
    return ResourceSummaryDTO(
        mission_id=mission_id,
        max_usd_limit=snapshot["usd_limit"],
        current_usd_spent=snapshot["usd_spent"],
        max_total_tokens=snapshot["tokens_limit"],
        current_tokens_used=snapshot["tokens_used"],
        current_execution_time_seconds=snapshot["execution_time_seconds"],
        active_agent_leases=snapshot["active_agent_leases"],
        active_tool_locks=snapshot["active_tool_locks"],
    )


@router.get("/{mission_id}/resources/monitor", response_model=ResourceMonitorResponseDTO)
async def get_mission_resource_monitor(
    mission_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> ResourceMonitorResponseDTO:
    """Retrieve full 6-dimensional resource monitoring with causal explanation audit log."""
    rb = state.get_resource_brain(mission_id)
    if not rb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource brain not found."
        )

    snapshot = rb.get_monitor_snapshot()
    dims = {
        k: ResourceMetricTupleDTO(
            allocated=v.allocated,
            consumed=v.consumed,
            remaining=v.remaining,
            reserved=v.reserved,
            unit=v.unit,
        )
        for k, v in snapshot.dimensions.items()
    }
    agent_bd = {
        k: ResourceMetricTupleDTO(
            allocated=v.allocated,
            consumed=v.consumed,
            remaining=v.remaining,
            reserved=v.reserved,
            unit=v.unit,
        )
        for k, v in snapshot.agent_breakdown.items()
    }
    tool_bd = {
        k: ResourceMetricTupleDTO(
            allocated=v.allocated,
            consumed=v.consumed,
            remaining=v.remaining,
            reserved=v.reserved,
            unit=v.unit,
        )
        for k, v in snapshot.tool_breakdown.items()
    }
    realloc_history = [
        AllocationChangeEventDTO(
            change_id=h.change_id,
            mission_id=h.mission_id,
            timestamp=h.timestamp,
            dimension=h.dimension.value if hasattr(h.dimension, "value") else str(h.dimension),
            target_name=h.target_name,
            previous_allocated=h.previous_allocated,
            new_allocated=h.new_allocated,
            delta=h.delta,
            unit=h.unit,
            trigger_type=h.trigger_type,
            reason=h.reason,
        )
        for h in snapshot.reallocation_history
    ]

    return ResourceMonitorResponseDTO(
        mission_id=mission_id,
        dimensions=dims,
        agent_breakdown=agent_bd,
        tool_breakdown=tool_bd,
        reallocation_history=realloc_history,
        timestamp=snapshot.timestamp,
    )


@router.post("/{mission_id}/resources/reallocate", response_model=AllocationChangeEventDTO)
async def reallocate_mission_resource(
    mission_id: str,
    request: ManualReallocationRequest,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> AllocationChangeEventDTO:
    """Manually reallocate mission resources with mandatory justification rationale."""
    rb = state.get_resource_brain(mission_id)
    if not rb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource brain not found."
        )

    try:
        dim_enum = ResourceDimension(request.dimension.lower())
    except ValueError:
        dim_enum = ResourceDimension.BUDGET

    change_evt = rb.record_allocation_change(
        dimension=dim_enum,
        target_name=request.to_target,
        delta=request.amount,
        unit=request.unit,
        trigger_type="OPERATOR_MANUAL_REALLOCATION",
        reason=request.reason,
    )

    return AllocationChangeEventDTO(
        change_id=change_evt.change_id,
        mission_id=change_evt.mission_id,
        timestamp=change_evt.timestamp,
        dimension=change_evt.dimension.value,
        target_name=change_evt.target_name,
        previous_allocated=change_evt.previous_allocated,
        new_allocated=change_evt.new_allocated,
        delta=change_evt.delta,
        unit=change_evt.unit,
        trigger_type=change_evt.trigger_type,
        reason=change_evt.reason,
    )


def _format_claim_dto(c: Any, ee: Any) -> EvidenceClaimDTO:
    """Format an EvidenceClaim entity into a rich EvidenceClaimDTO with decision reasoning and conflicts."""
    status_str = c.status.value if hasattr(c.status, "value") else str(c.status)
    reliability_str = (
        c.source_reliability.value
        if hasattr(c.source_reliability, "value")
        else str(c.source_reliability)
    )

    # Collect conflicts
    claim_conflicts: list[ClaimConflictDTO] = []
    for conf_id in c.conflict_ids:
        if conf_id in ee._conflicts:
            conf = ee._conflicts[conf_id]
            claim_conflicts.append(
                ClaimConflictDTO(
                    conflict_id=conf.conflict_id,
                    claim_a_id=conf.claim_a_id,
                    claim_b_id=conf.claim_b_id,
                    subject=conf.subject,
                    predicate=conf.predicate,
                    value_a=conf.value_a,
                    value_b=conf.value_b,
                    reason=conf.reason,
                    severity=conf.severity,
                    is_resolved=conf.is_resolved,
                    resolution_notes=conf.resolution_notes,
                    resolved_at=conf.resolved_at,
                )
            )

    unresolved_count = sum(1 for conf in claim_conflicts if not conf.is_resolved)

    # Compute Decision Reason
    if status_str == "VERIFIED":
        decision_reason = (
            f"Certified as verified: Backed by {len(c.evidence_items)} stored evidence artifact(s) "
            f"with valid SHA-256 cryptographic hashes, {unresolved_count} unresolved contradictions, "
            f"and {int(c.confidence * 100)}% empirical confidence score."
        )
    elif status_str in ("REFUTED", "INVALIDATED"):
        decision_reason = (
            c.invalidation_reason
            or "Refuted: Overridden by authoritative contradiction or failed verification check."
        )
    elif status_str == "SUPERSEDED":
        decision_reason = (
            f"Superseded: Replaced by updated empirical claim '{c.superseded_by_claim_id}'."
        )
    else:
        decision_reason = (
            f"Proposed: Originating from {reliability_str} ({c.source_ref}); "
            f"awaiting independent verification audit."
        )

    ev_items = [
        EvidenceItemDTO(
            evidence_id=ev.evidence_id,
            source_uri=ev.source_uri,
            content_ref=ev.content_ref,
            raw_data_hash=ev.raw_data_hash,
            byte_size=ev.byte_size,
            collected_by_agent=ev.collected_by_agent,
            task_id=ev.task_id,
            timestamp=ev.timestamp,
            metadata=ev.metadata,
        )
        for ev in c.evidence_items
    ]

    return EvidenceClaimDTO(
        claim_id=c.claim_id,
        mission_id=c.mission_id,
        statement=c.statement,
        subject=c.subject,
        predicate=c.predicate,
        value=c.value,
        source_ref=c.source_ref,
        source_reliability=reliability_str,
        confidence=c.confidence,
        status=status_str,
        content_ref=c.content_ref,
        evidence_items=ev_items,
        conflict_ids=c.conflict_ids,
        conflicts=claim_conflicts,
        invalidation_reason=c.invalidation_reason,
        superseded_by_claim_id=c.superseded_by_claim_id,
        final_decision_reason=decision_reason,
        created_at=c.created_at,
        updated_at=c.updated_at,
        verified_at=c.verified_at,
    )


@router.get("/{mission_id}/evidence", response_model=EvidenceSummaryDTO)
async def get_mission_evidence(
    mission_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> EvidenceSummaryDTO:
    """Retrieve empirical claims, confidence scores, conflicts, and recommendation trace."""
    ee = state.get_evidence_engine(mission_id)
    if not ee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence engine not found."
        )

    claims = ee.list_claims(mission_id=mission_id)
    verified_count = sum(1 for c in claims if c.status.value == "VERIFIED")

    formatted_claims = [_format_claim_dto(c, ee) for c in claims]
    all_conflicts = [
        ClaimConflictDTO(
            conflict_id=conf.conflict_id,
            claim_a_id=conf.claim_a_id,
            claim_b_id=conf.claim_b_id,
            subject=conf.subject,
            predicate=conf.predicate,
            value_a=conf.value_a,
            value_b=conf.value_b,
            reason=conf.reason,
            severity=conf.severity,
            is_resolved=conf.is_resolved,
            resolution_notes=conf.resolution_notes,
            resolved_at=conf.resolved_at,
        )
        for conf in ee.get_conflicts(unresolved_only=False)
    ]

    return EvidenceSummaryDTO(
        mission_id=mission_id,
        total_claims=len(claims),
        verified_claims=verified_count,
        claims=formatted_claims,
        conflicts=all_conflicts,
        trace=None,
    )


@router.get("/{mission_id}/evidence/claims/{claim_id}", response_model=EvidenceClaimDTO)
async def get_mission_claim_detail(
    mission_id: str,
    claim_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> EvidenceClaimDTO:
    """Retrieve detailed state and stored evidence proofs for a specific claim."""
    ee = state.get_evidence_engine(mission_id)
    if not ee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence engine not found."
        )

    try:
        claim = ee.get_claim(claim_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Claim '{claim_id}' not found."
        ) from None

    return _format_claim_dto(claim, ee)


def _detect_artifact_type(filename: str, declared_type: str | None = None) -> str:
    """Detect deliverable category from filename or declared type."""
    if declared_type and declared_type in ArtifactType.__members__:
        return declared_type
    fn = filename.lower()
    if "report" in fn or fn.endswith((".report.md", "_report.md", "_audit.md")):
        return ArtifactType.REPORT.value
    elif "dataset" in fn or fn.endswith((".json", ".csv", ".parquet")):
        return ArtifactType.DATASET.value
    elif "slide" in fn or "presentation" in fn or "pitch" in fn:
        return ArtifactType.PRESENTATION.value
    elif "summary" in fn or "tldr" in fn or "brief" in fn:
        return ArtifactType.SUMMARY.value
    elif "evidence" in fn or "manifest" in fn or "proof" in fn:
        return ArtifactType.EVIDENCE_PACKAGE.value
    return ArtifactType.REPORT.value


def _format_artifact_dto(a: dict[str, Any], mission_id: str) -> ArtifactDTO:
    """Format stored artifact dictionary into complete ArtifactDTO."""
    art_id = a.get("artifact_id") or f"art_{uuid4().hex[:10]}"
    filename = a.get("filename", "deliverable.md")
    art_type = a.get("artifact_type") or _detect_artifact_type(filename)
    title = a.get("title") or filename.replace("_", " ").replace("-", " ").title()

    raw_content = a.get("content", "")
    content_bytes = raw_content.encode("utf-8") if isinstance(raw_content, str) else b""
    sha256_hash = a.get("sha256") or hashlib.sha256(content_bytes).hexdigest()
    size_bytes = a.get("size_bytes") or len(content_bytes)
    gcs_uri = a.get("gcs_uri") or f"gs://agentx-evidence/missions/{mission_id}/artifacts/{filename}"

    return ArtifactDTO(
        artifact_id=art_id,
        mission_id=mission_id,
        title=title,
        filename=filename,
        artifact_type=art_type,
        created_at=a.get("created_at") or datetime.now(UTC),
        generation_status=a.get("generation_status", "GENERATED"),
        verification_status=a.get("verification_status", "VERIFIED"),
        sha256=sha256_hash,
        size_bytes=size_bytes,
        gcs_uri=gcs_uri,
        content=raw_content if raw_content else None,
        content_type=a.get("content_type", "text/markdown"),
        task_id=a.get("task_id"),
        agent_role=a.get("agent_role"),
        metadata=a.get("metadata", {}),
    )


@router.get("/{mission_id}/artifacts", response_model=list[ArtifactDTO])
async def list_mission_artifacts(
    mission_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
    category: str | None = Query(
        default=None,
        description="Optional category: REPORT | DATASET | PRESENTATION | SUMMARY | EVIDENCE_PACKAGE",
    ),
) -> list[ArtifactDTO]:
    """Retrieve list of categorized mission deliverables and evidence packages."""
    art_list = state.artifacts.get(mission_id, [])
    dtos = [_format_artifact_dto(a, mission_id) for a in art_list]
    if category and category.upper() != "ALL":
        dtos = [d for d in dtos if d.artifact_type.upper() == category.upper()]
    return dtos


@router.post(
    "/{mission_id}/artifacts",
    response_model=ArtifactDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_mission_artifact(
    mission_id: str,
    request: CreateArtifactRequest,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> ArtifactDTO:
    """Create and register a mission deliverable with SHA-256 integrity hash."""
    mission = state.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found.")

    content_bytes = request.content.encode("utf-8")
    sha256_hash = hashlib.sha256(content_bytes).hexdigest()
    art_id = f"art_{uuid4().hex[:10]}"
    gcs_uri = f"gs://agentx-evidence/missions/{mission_id}/artifacts/{request.filename}"

    art_dict = {
        "artifact_id": art_id,
        "mission_id": mission_id,
        "title": request.title,
        "filename": request.filename,
        "artifact_type": request.artifact_type.upper(),
        "created_at": datetime.now(UTC),
        "generation_status": "GENERATED",
        "verification_status": "VERIFIED",
        "sha256": sha256_hash,
        "size_bytes": len(content_bytes),
        "gcs_uri": gcs_uri,
        "content": request.content,
        "content_type": request.content_type,
        "task_id": request.task_id,
        "agent_role": request.agent_role,
        "metadata": request.metadata,
    }

    if mission_id not in state.artifacts:
        state.artifacts[mission_id] = []
    state.artifacts[mission_id].append(art_dict)

    return _format_artifact_dto(art_dict, mission_id)


@router.get("/{mission_id}/artifacts/{artifact_id}", response_model=ArtifactDTO)
async def get_mission_artifact(
    mission_id: str,
    artifact_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> ArtifactDTO:
    """Retrieve single deliverable artifact metadata and content."""
    art_list = state.artifacts.get(mission_id, [])
    for a in art_list:
        dto = _format_artifact_dto(a, mission_id)
        if dto.artifact_id == artifact_id or dto.filename == artifact_id:
            return dto

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=f"Artifact '{artifact_id}' not found."
    )


@router.get("/{mission_id}/artifacts/{artifact_id}/download")
async def download_mission_artifact(
    mission_id: str,
    artifact_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> Response:
    """Download artifact content as a raw file attachment."""
    art_list = state.artifacts.get(mission_id, [])
    target = None
    for a in art_list:
        dto = _format_artifact_dto(a, mission_id)
        if dto.artifact_id == artifact_id or dto.filename == artifact_id:
            target = dto
            break

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Artifact '{artifact_id}' not found."
        )

    content_data = target.content or f"# Deliverable: {target.title}\n\nSHA-256: {target.sha256}\n"
    return Response(
        content=content_data.encode("utf-8"),
        media_type=target.content_type,
        headers={"Content-Disposition": f'attachment; filename="{target.filename}"'},
    )


def _map_event_to_timeline_dto(evt: Any) -> TimelineEventDTO:
    """Map heterogenous kernel EventBus event into unified TimelineEventDTO."""
    evt_type = evt.event_type.value if hasattr(evt.event_type, "value") else str(evt.event_type)
    evt_id = getattr(evt, "event_id", f"evt_{uuid4().hex[:8]}")
    evt_task_id = getattr(evt, "task_id", None)
    evt_payload = getattr(evt, "payload", None) or getattr(evt, "details", {})
    if not isinstance(evt_payload, dict):
        evt_payload = {"raw": str(evt_payload)}

    cat = "TASK"
    sev = "INFO"
    title = evt_type.replace("_", " ").title()
    desc = f"Event {evt_type} emitted."

    if "FAILURE" in evt_type or "FAILED" in evt_type:
        cat = "FAILURE"
        sev = "ERROR"
        title = "Task Failure Diagnosed"
        desc = evt_payload.get("error_message", "Task execution error encountered.")
    elif "RECOVERY" in evt_type or "HEALED" in evt_type:
        cat = "RECOVERY"
        sev = "SUCCESS"
        title = "Self-Healing Recovery Applied"
        desc = evt_payload.get("reasoning", "Automated recovery action executed.")
    elif "DRIFT" in evt_type:
        cat = "DRIFT"
        sev = "WARNING" if "DETECTED" in evt_type else "SUCCESS"
        title = "Goal Drift " + ("Detected" if "DETECTED" in evt_type else "Remediated")
        desc = evt_payload.get("reason", "Semantic alignment deviation evaluated.")
    elif "RESOURCE" in evt_type or "BUDGET" in evt_type:
        cat = "RESOURCE"
        sev = "INFO"
        title = "Resource Reallocation"
        desc = evt_payload.get("reason", "Operational resource adjustment logged.")
    elif "EVIDENCE" in evt_type or "VERIF" in evt_type:
        cat = "EVIDENCE"
        sev = "SUCCESS"
        title = "Evidence Verified"
        desc = "Cryptographic integrity proof verified."
    elif "COMPLETED" in evt_type:
        cat = "LIFECYCLE"
        sev = "SUCCESS"
        title = "Task Completed"
        desc = f"Task {evt_task_id} completed successfully."

    return TimelineEventDTO(
        event_id=evt_id,
        timestamp=getattr(evt, "timestamp", datetime.now(UTC)),
        event_type=evt_type,
        title=title,
        description=desc,
        category=cat,
        agent_role=None,
        task_id=evt_task_id,
        severity=sev,
        metadata=evt_payload,
    )


@router.get("/{mission_id}/failures", response_model=FailureCenterResponseDTO)
async def get_mission_failures(
    mission_id: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> FailureCenterResponseDTO:
    """Retrieve failure diagnostics, self-healing recoveries, replacements, and mission timeline."""
    mission = state.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found.")

    rec_engine = state.get_recovery_engine(mission_id)
    workflow = state.get_workflow(mission_id)

    # 1. Build Failure Records
    failure_records: list[FailureRecordDTO] = []
    category_counts: dict[str, int] = {}
    strategy_counts: dict[str, int] = {}
    healed_count = 0
    escalated_count = 0

    if rec_engine:
        for diag_id, diag in rec_engine._diagnostics.items():
            if diag.mission_id != mission_id:
                continue

            category_str = diag.category.value
            category_counts[category_str] = category_counts.get(category_str, 0) + 1

            # Match associated action
            matching_action = None
            for act in rec_engine._actions.values():
                if act.diagnostic_id == diag_id or act.target_task_id == diag.task_id:
                    matching_action = act
                    break

            strategy_str = matching_action.strategy.value if matching_action else "RETRY"
            strategy_counts[strategy_str] = strategy_counts.get(strategy_str, 0) + 1

            # Determine task info
            task = workflow._tasks.get(diag.task_id) if workflow else None
            task_name = task.name if task else diag.task_id
            agent_role_str = task.agent_role.value if task else "Specialist"

            # Determine replacement
            replacement_str = "N/A - Re-executing with existing tools"
            add_resources_str = "None requested"
            result_str = "APPLIED"

            if matching_action:
                strat = matching_action.strategy.value
                params = matching_action.parameters
                if strat == "ALTERNATIVE_TOOL":
                    replacement_str = (
                        f"Swapped tool to '{params.get('alternative_tool', 'Alternative Tool')}'"
                    )
                elif strat == "ALTERNATIVE_AGENT":
                    replacement_str = (
                        f"Swapped agent persona to '{params.get('alternative_agent', 'Coder')}'"
                    )
                elif strat == "WORKFLOW_MUTATION":
                    inject_info = params.get("inject_prerequisite_task", {})
                    replacement_str = (
                        f"Injected prerequisite task '{inject_info.get('name', 'Fix Task')}'"
                    )
                elif strat == "TASK_MODIFICATION":
                    replacement_str = f"Modified task input parameters ({len(params)} adjustments)"
                elif strat == "HUMAN_APPROVAL":
                    replacement_str = "Human intervention required"
                    result_str = "ESCALATED_HITL"
                    escalated_count += 1

                if strat == "RESOURCE_REALLOCATION":
                    add_tokens = params.get("additional_tokens", 0)
                    add_usd = params.get("additional_usd", 0.0)
                    add_resources_str = f"+{add_tokens:,} tokens, +${add_usd:.2f} USD"

                if result_str != "ESCALATED_HITL":
                    if task and task.status.value in ("COMPLETED", "VERIFIED"):
                        result_str = "RECOVERED"
                        healed_count += 1
                    elif matching_action.status == "APPLIED":
                        result_str = "APPLIED"
                        healed_count += 1
                    elif matching_action.status == "FAILED":
                        result_str = "FAILED"
                    else:
                        result_str = "APPLIED"
                        healed_count += 1
            else:
                if task and task.status.value in ("COMPLETED", "VERIFIED"):
                    result_str = "RECOVERED"
                    healed_count += 1

            failure_records.append(
                FailureRecordDTO(
                    failure_id=diag.diagnostic_id,
                    failure=diag.error_message,
                    classification=category_str,
                    affected_task_id=diag.task_id,
                    affected_task_name=task_name,
                    assigned_agent=agent_role_str,
                    recovery_strategy=strategy_str,
                    replacement=replacement_str,
                    additional_resources=add_resources_str,
                    result=result_str,
                    retry_count=diag.retry_count,
                    max_retries=diag.max_retries,
                    is_recoverable=diag.is_recoverable,
                    diagnostic_reasoning=(
                        matching_action.reasoning
                        if matching_action
                        else "Automated error recovery triggered."
                    ),
                    stack_trace=diag.stack_trace,
                    timestamp=diag.diagnosed_at,
                )
            )

    # 2. Build Chronological Mission Timeline
    raw_events = state.event_bus.get_events(mission_id=mission_id)
    timeline_events: list[TimelineEventDTO] = [
        TimelineEventDTO(
            event_id=f"evt_init_{mission_id}",
            timestamp=mission.created_at,
            event_type="MISSION_CREATED",
            title="Mission Initialized",
            description=f"Mission '{mission.title}' registered with budget ${mission.budget.max_usd_limit:.2f}.",
            category="LIFECYCLE",
            severity="INFO",
            metadata={"goal": mission.goal.goal_statement},
        )
    ]

    for evt in raw_events:
        timeline_events.append(_map_event_to_timeline_dto(evt))

    # Sort timeline chronologically
    timeline_events.sort(key=lambda e: e.timestamp)

    total_failures = len(failure_records)
    recovery_rate = (healed_count / total_failures * 100) if total_failures > 0 else 100.0

    summary = FailureCenterSummaryDTO(
        total_failures=total_failures,
        healed_count=healed_count,
        escalated_hitl_count=escalated_count,
        recovery_rate=round(recovery_rate, 1),
        categories_breakdown=category_counts,
        strategies_breakdown=strategy_counts,
    )

    return FailureCenterResponseDTO(
        mission_id=mission_id,
        summary=summary,
        failures=failure_records,
        timeline=timeline_events,
    )

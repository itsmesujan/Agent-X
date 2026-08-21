"""Human-in-the-Loop Approvals API Routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from agentx.api.auth import AuthUser, get_current_user
from agentx.api.schemas import ApprovalDecisionRequest, ApprovalDecisionResponse
from agentx.api.state import ApiStateManager, state_manager
from agentx.kernel.events import EventType, KernelEvent
from agentx.kernel.state_machine import MissionStateMachine
from agentx_common.schemas import MissionStatus

router = APIRouter(prefix="/approvals", tags=["Approvals"])


def get_state() -> ApiStateManager:
    return state_manager


@router.post("/{approval_id}/approve", response_model=ApprovalDecisionResponse)
async def approve_hitl_escalation(
    approval_id: str,
    request: ApprovalDecisionRequest,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> ApprovalDecisionResponse:
    """Approve a pending HITL escalation and resume mission execution."""
    approval = state.get_approval(approval_id)
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval with ID '{approval_id}' was not found.",
        )

    approval.status = "APPROVED"
    approval.decision_notes = request.decision_notes or "Approved by operator"

    # Resume the associated mission if it was paused
    mission = state.get_mission(approval.mission_id)
    if mission and mission.state.status == MissionStatus.PAUSED:
        evt = MissionStateMachine.transition(
            mission, MissionStatus.EXECUTING, reason="Resumed upon HITL approval"
        )
        state.event_bus.publish(evt)

    # Publish approval resolution event
    state.event_bus.publish(
        KernelEvent(
            mission_id=approval.mission_id,
            event_type=EventType.MISSION_STATE_CHANGED,
            payload={
                "approval_id": approval_id,
                "status": "APPROVED",
                "operator_email": current_user.email,
                "decision_notes": approval.decision_notes,
            },
        )
    )

    return ApprovalDecisionResponse(
        approval_id=approval.approval_id,
        mission_id=approval.mission_id,
        status="APPROVED",
        decision_notes=approval.decision_notes,
    )


@router.post("/{approval_id}/reject", response_model=ApprovalDecisionResponse)
async def reject_hitl_escalation(
    approval_id: str,
    request: ApprovalDecisionRequest,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    state: Annotated[ApiStateManager, Depends(get_state)],
) -> ApprovalDecisionResponse:
    """Reject a pending HITL escalation, keeping mission paused or aborted."""
    approval = state.get_approval(approval_id)
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval with ID '{approval_id}' was not found.",
        )

    approval.status = "REJECTED"
    approval.decision_notes = request.decision_notes or "Rejected by operator"

    # Publish rejection event
    state.event_bus.publish(
        KernelEvent(
            mission_id=approval.mission_id,
            event_type=EventType.MISSION_STATE_CHANGED,
            payload={
                "approval_id": approval_id,
                "status": "REJECTED",
                "operator_email": current_user.email,
                "decision_notes": approval.decision_notes,
            },
        )
    )

    return ApprovalDecisionResponse(
        approval_id=approval.approval_id,
        mission_id=approval.mission_id,
        status="REJECTED",
        decision_notes=approval.decision_notes,
    )

"""Unit tests for Kernel Events and EventBus."""

from agentx.kernel.events import (
    EventBus,
    EventType,
    HITLEscalationEvent,
    KernelEvent,
    MissionStateTransitionEvent,
    TaskStateTransitionEvent,
)
from agentx_common.schemas import MissionStatus, TaskStatus


def test_event_bus_subscribe_and_publish() -> None:
    bus = EventBus()
    received_state_events: list[KernelEvent] = []
    received_all_events: list[KernelEvent] = []

    bus.subscribe(
        EventType.MISSION_STATE_CHANGED,
        lambda evt: received_state_events.append(evt),
    )
    bus.subscribe_all(lambda evt: received_all_events.append(evt))

    evt = MissionStateTransitionEvent(
        mission_id="msn_123",
        from_status=MissionStatus.DRAFT,
        to_status=MissionStatus.PARSING_GOAL,
        reason="Initialized",
    )

    bus.publish(evt)

    assert len(received_state_events) == 1
    assert len(received_all_events) == 1
    assert received_state_events[0].mission_id == "msn_123"

    events = bus.get_events(mission_id="msn_123")
    assert len(events) == 1


def test_task_state_transition_event() -> None:
    evt = TaskStateTransitionEvent(
        mission_id="msn_456",
        task_id="task_01",
        from_status=TaskStatus.PENDING,
        to_status=TaskStatus.READY,
    )
    assert evt.event_type == EventType.TASK_STATE_CHANGED
    assert evt.task_id == "task_01"
    assert evt.to_status == TaskStatus.READY


def test_hitl_escalation_event() -> None:
    evt = HITLEscalationEvent(
        mission_id="msn_789",
        task_id="task_99",
        error_class="AuthTokenExpiredError",
        diagnosis="GCP OAuth access token has expired and cannot be auto-refreshed",
        suggested_actions=["Re-authenticate via gcloud auth application-default login"],
    )
    assert evt.event_type == EventType.HITL_ESCALATION
    assert len(evt.suggested_actions) == 1

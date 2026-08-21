"""Google Cloud Pub/Sub Typed Event Publisher for Agent-X."""

import json
from typing import Any

from agentx.gcp.pubsub.client import MockPubSubClient
from agentx.gcp.pubsub.topics import PubSubTopic
from agentx.kernel.events import EventType, KernelEvent


class PubSubEventPublisher:
    """Publishes domain events to dedicated Google Cloud Pub/Sub topics with ordering keys."""

    def __init__(self, client: MockPubSubClient | Any) -> None:
        self.client = client

    def _publish_raw(
        self,
        topic: str,
        event: KernelEvent,
        ordering_key: str | None = None,
    ) -> str:
        payload_bytes = json.dumps(event.model_dump(mode="json")).encode("utf-8")
        msg_id = self.client.publish(
            topic_name=topic,
            data=payload_bytes,
            ordering_key=ordering_key or event.mission_id,
            event_type=event.event_type.value
            if hasattr(event.event_type, "value")
            else str(event.event_type),
            mission_id=event.mission_id,
        )
        return str(msg_id)

    def publish_mission_event(self, event: KernelEvent) -> str:
        """Publish mission lifecycle and status events."""
        return self._publish_raw(PubSubTopic.MISSION_EVENTS.value, event)

    def publish_task_event(self, event: KernelEvent) -> str:
        """Publish task DAG mutations, dispatch, and completion events."""
        return self._publish_raw(PubSubTopic.TASK_EVENTS.value, event)

    def publish_agent_event(self, event: KernelEvent) -> str:
        """Publish subagent invocation, thoughts, and tool execution metrics."""
        return self._publish_raw(PubSubTopic.AGENT_EVENTS.value, event)

    def publish_recovery_event(self, event: KernelEvent) -> str:
        """Publish failure diagnostics, self-healing, and drift remediation events."""
        return self._publish_raw(PubSubTopic.RECOVERY_EVENTS.value, event)

    def route_and_publish(self, event: KernelEvent) -> str:
        """Intelligently route any domain event to its corresponding topic based on event type."""
        e_type = event.event_type

        # Recovery & Drift events
        if e_type in (
            EventType.FAILURE_DIAGNOSED,
            EventType.RECOVERY_APPLIED,
            EventType.GOAL_DRIFT_DETECTED,
            EventType.GOAL_DRIFT_REMEDIATED,
        ):
            return self.publish_recovery_event(event)

        # Task events
        elif e_type in (
            EventType.TASK_CREATED,
            EventType.TASK_STATE_CHANGED,
            EventType.WORKFLOW_INITIALIZED,
            EventType.WORKFLOW_MUTATED,
            EventType.VERIFICATION_RECORDED,
        ):
            return self.publish_task_event(event)

        # Agent & Tool events
        elif e_type in (
            EventType.TOOL_INVOKED,
            EventType.TOOL_FAILED,
            EventType.HUMAN_ATTENTION_REQUESTED,
        ):
            return self.publish_agent_event(event)

        # Mission events (default)
        else:
            return self.publish_mission_event(event)

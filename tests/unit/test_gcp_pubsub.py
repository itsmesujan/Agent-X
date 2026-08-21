"""Unit tests for Google Cloud Pub/Sub Publisher and Subscriber Infrastructure."""

import pytest

from agentx.gcp.pubsub import (
    MockPubSubClient,
    PubSubClientFactory,
    PubSubEventPublisher,
    PubSubEventSubscriber,
    PubSubTopic,
)
from agentx.kernel.events import EventType, KernelEvent


@pytest.fixture
def pubsub_client() -> MockPubSubClient:
    return PubSubClientFactory.create_client(use_mock=True)


def test_pubsub_topic_creation_and_routing(pubsub_client: MockPubSubClient) -> None:
    """Test PubSubEventPublisher routing events to mission-events, task-events, agent-events, recovery-events."""
    publisher = PubSubEventPublisher(client=pubsub_client)

    # 1. Mission Event -> agentx-mission-events
    e_mission = KernelEvent(
        mission_id="msn_001",
        event_type=EventType.MISSION_STATE_CHANGED,
        payload={"title": "Test Mission"},
    )
    publisher.route_and_publish(e_mission)
    assert len(pubsub_client.published_messages[PubSubTopic.MISSION_EVENTS.value]) == 1

    # 2. Task Event -> agentx-task-events
    e_task = KernelEvent(
        mission_id="msn_001",
        event_type=EventType.TASK_CREATED,
        payload={"task_id": "t1"},
    )
    publisher.route_and_publish(e_task)
    assert len(pubsub_client.published_messages[PubSubTopic.TASK_EVENTS.value]) == 1

    # 3. Agent & Tool Event -> agentx-agent-events
    e_agent = KernelEvent(
        mission_id="msn_001",
        event_type=EventType.TOOL_INVOKED,
        payload={"tool_name": "web_research"},
    )
    publisher.route_and_publish(e_agent)
    assert len(pubsub_client.published_messages[PubSubTopic.AGENT_EVENTS.value]) == 1

    # 4. Recovery Event -> agentx-recovery-events
    e_rec = KernelEvent(
        mission_id="msn_001",
        event_type=EventType.FAILURE_DIAGNOSED,
        payload={"category": "TRANSIENT"},
    )
    publisher.route_and_publish(e_rec)
    assert len(pubsub_client.published_messages[PubSubTopic.RECOVERY_EVENTS.value]) == 1


def test_pubsub_subscriber_consumption_and_ack(pubsub_client: MockPubSubClient) -> None:
    """Test PubSubEventSubscriber pulling messages, invoking callbacks, and committing acks."""
    # Create subscription
    sub = pubsub_client.create_subscription(
        subscription_name="sub-task-workers",
        topic_name=PubSubTopic.TASK_EVENTS.value,
    )

    publisher = PubSubEventPublisher(client=pubsub_client)
    subscriber = PubSubEventSubscriber(
        client=pubsub_client,
        subscription_name="sub-task-workers",
    )

    consumed_events: list[KernelEvent] = []
    subscriber.register_handler(lambda e: consumed_events.append(e))

    # Publish 3 task events
    for i in range(3):
        e = KernelEvent(
            mission_id="msn_002",
            event_type=EventType.TASK_CREATED,
            payload={"index": i},
        )
        publisher.publish_task_event(e)

    # Process batch
    processed_count = subscriber.process_batch(max_messages=10)
    assert processed_count == 3
    assert len(consumed_events) == 3
    assert sub.acknowledged_count == 3
    assert len(sub._queue) == 0


def test_pubsub_dlq_dead_letter_queue_threshold(pubsub_client: MockPubSubClient) -> None:
    """Test messages exceeding max_delivery_attempts are routed to DLQ."""
    sub = pubsub_client.create_subscription(
        subscription_name="sub-flaky-worker",
        topic_name=PubSubTopic.TASK_EVENTS.value,
        max_delivery_attempts=2,
        dead_letter_topic=PubSubTopic.DEAD_LETTER_QUEUE.value,
    )

    publisher = PubSubEventPublisher(client=pubsub_client)
    subscriber = PubSubEventSubscriber(
        client=pubsub_client,
        subscription_name="sub-flaky-worker",
    )

    # Register a handler that always raises an error (simulating poison pill / worker crash)
    def failing_handler(e: KernelEvent) -> None:
        raise RuntimeError("Poison pill failure")

    subscriber.register_handler(failing_handler)

    publisher.publish_task_event(
        KernelEvent(
            mission_id="msn_003",
            event_type=EventType.TASK_CREATED,
            payload={"poison": True},
        )
    )

    # Attempt 1 -> fails, nacked back to queue
    subscriber.process_batch()
    assert sub.acknowledged_count == 0

    # Attempt 2 -> fails, nacked back to queue
    subscriber.process_batch()
    assert sub.acknowledged_count == 0

    # Attempt 3 -> exceeds max_delivery_attempts (2) -> dropped from queue and forwarded to DLQ
    subscriber.process_batch()
    assert sub.dlq_forwarded_count == 1
    assert len(sub._queue) == 0

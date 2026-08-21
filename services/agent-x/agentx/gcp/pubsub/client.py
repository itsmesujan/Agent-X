"""Google Cloud Pub/Sub Client Abstraction and Mock/Emulator Adapter."""

import importlib
import threading
from collections import deque
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


class PubSubMessage:
    """Represents a Pub/Sub message payload with metadata."""

    def __init__(
        self,
        message_id: str,
        data: bytes,
        attributes: dict[str, str] | None = None,
        ordering_key: str | None = None,
        published_at: datetime | None = None,
    ) -> None:
        self.message_id = message_id
        self.data = data
        self.attributes = attributes or {}
        self.ordering_key = ordering_key
        self.published_at = published_at or datetime.now(UTC)
        self.ack_id = f"ack_{uuid4().hex[:12]}"
        self.delivery_count = 0


class MockPubSubSubscription:
    """Mock pull subscription with message buffering, ack, nack, and DLQ support."""

    def __init__(
        self,
        subscription_name: str,
        topic_name: str,
        max_delivery_attempts: int = 5,
        dead_letter_topic: str | None = None,
    ) -> None:
        self.subscription_name = subscription_name
        self.topic_name = topic_name
        self.max_delivery_attempts = max_delivery_attempts
        self.dead_letter_topic = dead_letter_topic
        self._lock = threading.RLock()
        self._queue: deque[PubSubMessage] = deque()
        self._in_flight: dict[str, PubSubMessage] = {}  # ack_id -> message
        self.acknowledged_count = 0
        self.dlq_forwarded_count = 0

    def enqueue(self, message: PubSubMessage) -> None:
        with self._lock:
            self._queue.append(message)

    def pull(self, max_messages: int = 10) -> list[PubSubMessage]:
        with self._lock:
            pulled: list[PubSubMessage] = []
            while self._queue and len(pulled) < max_messages:
                msg = self._queue.popleft()
                msg.delivery_count += 1

                # Check if message exceeded max delivery attempts
                if msg.delivery_count > self.max_delivery_attempts:
                    self.dlq_forwarded_count += 1
                    continue

                self._in_flight[msg.ack_id] = msg
                pulled.append(msg)
            return pulled

    def acknowledge(self, ack_ids: list[str]) -> None:
        with self._lock:
            for ack_id in ack_ids:
                if ack_id in self._in_flight:
                    del self._in_flight[ack_id]
                    self.acknowledged_count += 1

    def modify_ack_deadline(self, ack_ids: list[str], ack_deadline_seconds: int) -> None:
        """If ack_deadline_seconds == 0, nack the message back to queue for redelivery."""
        with self._lock:
            for ack_id in ack_ids:
                if ack_id in self._in_flight:
                    msg = self._in_flight.pop(ack_id)
                    if ack_deadline_seconds == 0:
                        self._queue.append(msg)


class MockPubSubClient:
    """Thread-safe In-Memory Google Cloud Pub/Sub Client for local testing."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.topics: set[str] = set()
        self.subscriptions: dict[str, MockPubSubSubscription] = {}
        self.published_messages: dict[str, list[PubSubMessage]] = {}  # topic -> list[PubSubMessage]

    def create_topic(self, topic_name: str) -> None:
        with self._lock:
            self.topics.add(topic_name)
            if topic_name not in self.published_messages:
                self.published_messages[topic_name] = []

    def create_subscription(
        self,
        subscription_name: str,
        topic_name: str,
        max_delivery_attempts: int = 5,
        dead_letter_topic: str | None = None,
    ) -> MockPubSubSubscription:
        with self._lock:
            sub = MockPubSubSubscription(
                subscription_name=subscription_name,
                topic_name=topic_name,
                max_delivery_attempts=max_delivery_attempts,
                dead_letter_topic=dead_letter_topic,
            )
            self.subscriptions[subscription_name] = sub
            return sub

    def publish(
        self,
        topic_name: str,
        data: bytes,
        ordering_key: str | None = None,
        **attributes: str,
    ) -> str:
        with self._lock:
            if topic_name not in self.topics:
                self.create_topic(topic_name)

            msg_id = f"msg_{uuid4().hex[:12]}"
            msg = PubSubMessage(
                message_id=msg_id,
                data=data,
                attributes=attributes,
                ordering_key=ordering_key,
            )
            self.published_messages[topic_name].append(msg)

            # Route to all subscriptions attached to this topic
            for sub in self.subscriptions.values():
                if sub.topic_name == topic_name:
                    sub.enqueue(msg)

            return msg_id

    def get_subscription(self, subscription_name: str) -> MockPubSubSubscription | None:
        with self._lock:
            return self.subscriptions.get(subscription_name)

    def clear(self) -> None:
        with self._lock:
            self.topics.clear()
            self.subscriptions.clear()
            self.published_messages.clear()


class PubSubClientFactory:
    """Factory creating Pub/Sub clients for live/emulator or local mocks."""

    @staticmethod
    def create_client(use_mock: bool = True) -> MockPubSubClient | Any:
        if use_mock:
            return MockPubSubClient()

        try:
            pubsub_module = importlib.import_module("google.cloud.pubsub_v1")
            return pubsub_module.PublisherClient()
        except Exception:
            return MockPubSubClient()

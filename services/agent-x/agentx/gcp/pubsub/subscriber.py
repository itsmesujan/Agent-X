"""Google Cloud Pub/Sub Event Subscriber for Worker Pool and Telemetry Consumers."""

import json
import logging
from collections.abc import Callable
from typing import Any

from agentx.gcp.pubsub.client import MockPubSubClient, MockPubSubSubscription
from agentx.kernel.events import KernelEvent

logger = logging.getLogger("agentx.pubsub.subscriber")


class PubSubEventSubscriber:
    """Consumes and routes typed domain events from Pub/Sub subscriptions."""

    def __init__(
        self,
        client: MockPubSubClient | Any,
        subscription_name: str,
    ) -> None:
        self.client = client
        self.subscription_name = subscription_name
        self._handlers: list[Callable[[KernelEvent], None]] = []

    def register_handler(self, handler: Callable[[KernelEvent], None]) -> None:
        """Register a callback handler for consumed events."""
        self._handlers.append(handler)

    def process_batch(self, max_messages: int = 10) -> int:
        """Pulls a batch of messages, invokes handlers, and commits acks/nacks."""
        sub: MockPubSubSubscription | None = (
            self.client.get_subscription(self.subscription_name)
            if hasattr(self.client, "get_subscription")
            else None
        )
        if not sub:
            return 0

        messages = sub.pull(max_messages=max_messages)
        if not messages:
            return 0

        ack_ids: list[str] = []
        nack_ids: list[str] = []

        for msg in messages:
            try:
                payload_dict = json.loads(msg.data.decode("utf-8"))
                event = KernelEvent.model_validate(payload_dict)

                for handler in self._handlers:
                    handler(event)

                ack_ids.append(msg.ack_id)
            except Exception as exc:
                logger.error(
                    f"Failed to process Pub/Sub message {msg.message_id}: {exc}", exc_info=True
                )
                nack_ids.append(msg.ack_id)

        if ack_ids:
            sub.acknowledge(ack_ids)
        if nack_ids:
            sub.modify_ack_deadline(nack_ids, ack_deadline_seconds=0)

        return len(ack_ids)

"""Unit tests for agentx_common constants."""

from agentx_common.constants import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_MISSION_TIMEOUT_SECONDS,
    DEFAULT_MISSION_TOKEN_CAP,
    DEFAULT_MISSION_USD_CAP,
    MODELS,
    PUBSUB_TOPICS,
)


def test_default_constants() -> None:
    assert DEFAULT_MISSION_USD_CAP == 5.00
    assert DEFAULT_MISSION_TOKEN_CAP == 1_000_000
    assert DEFAULT_MISSION_TIMEOUT_SECONDS == 3600
    assert DEFAULT_MAX_RETRIES == 3


def test_pubsub_topic_names() -> None:
    assert PUBSUB_TOPICS.TASK_DISPATCH == "agentx-task-dispatch"
    assert PUBSUB_TOPICS.TELEMETRY == "agentx-telemetry-events"
    assert PUBSUB_TOPICS.RECOVERY == "agentx-recovery-events"
    assert PUBSUB_TOPICS.DEAD_LETTER == "agentx-dead-letter-queue"


def test_model_names() -> None:
    assert MODELS.REASONING_PRO == "gemini-2.5-pro"
    assert MODELS.FAST_FLASH == "gemini-2.5-flash"

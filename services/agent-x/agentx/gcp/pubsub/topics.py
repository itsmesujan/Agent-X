"""Google Cloud Pub/Sub Topic Definitions for Agent-X."""

from enum import StrEnum


class PubSubTopic(StrEnum):
    """Standardized Agent-X Pub/Sub topic names."""

    MISSION_EVENTS = "agentx-mission-events"
    TASK_EVENTS = "agentx-task-events"
    AGENT_EVENTS = "agentx-agent-events"
    RECOVERY_EVENTS = "agentx-recovery-events"
    DEAD_LETTER_QUEUE = "agentx-dead-letter-queue"

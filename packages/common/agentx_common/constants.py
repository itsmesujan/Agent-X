"""Agent-X Common Constants."""

DEFAULT_MISSION_USD_CAP: float = 5.00
DEFAULT_MISSION_TOKEN_CAP: int = 1_000_000
DEFAULT_MISSION_TIMEOUT_SECONDS: int = 3600
DEFAULT_TASK_TIMEOUT_SECONDS: int = 300
DEFAULT_MAX_RETRIES: int = 3


class PUBSUB_TOPICS:
    TASK_DISPATCH = "agentx-task-dispatch"
    TELEMETRY = "agentx-telemetry-events"
    RECOVERY = "agentx-recovery-events"
    DEAD_LETTER = "agentx-dead-letter-queue"


class MODELS:
    REASONING_PRO = "gemini-2.5-pro"
    FAST_FLASH = "gemini-2.5-flash"
    FAST_FLASH_THINKING = "gemini-2.5-flash-thinking"
    FRONTIER_FLASH = "gemini-3.7-flash"
    FRONTIER_PRO = "gemini-3.1-pro"

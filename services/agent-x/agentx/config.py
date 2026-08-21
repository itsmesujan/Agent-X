"""Agent-X Configuration Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core
    environment: str = "development"
    debug: bool = True
    port: int = 8000
    log_level: str = "INFO"

    # GCP
    gcp_project_id: str = "agent-x-dev"
    gcp_region: str = "us-central1"

    # Gemini
    gemini_api_key: str = ""
    default_reasoning_model: str = "gemini-2.5-pro"
    default_fast_model: str = "gemini-2.5-flash"

    # Firestore
    firestore_database: str = "(default)"
    firestore_emulator_host: str | None = None

    # Pub/Sub
    pubsub_emulator_host: str | None = None
    pubsub_topic_task_dispatch: str = "agentx-task-dispatch-dev"
    pubsub_topic_telemetry: str = "agentx-telemetry-events-dev"
    pubsub_topic_recovery: str = "agentx-recovery-events-dev"
    pubsub_topic_dead_letter: str = "agentx-dead-letter-queue-dev"
    pubsub_subscription_worker: str = "agentx-worker-task-sub-dev"

    # GCS
    gcs_evidence_bucket: str = "agentx-evidence-artifacts-dev"

    # Budgets
    default_mission_usd_cap: float = 5.00
    default_mission_token_cap: int = 1_000_000
    default_mission_timeout_seconds: int = 3600

    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

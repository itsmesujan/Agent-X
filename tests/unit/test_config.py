"""Unit tests for agentx settings."""

from agentx.config import Settings


def test_default_settings() -> None:
    settings = Settings()
    assert settings.environment == "development"
    assert settings.port == 8000
    assert "http://localhost:3000" in settings.cors_origins_list

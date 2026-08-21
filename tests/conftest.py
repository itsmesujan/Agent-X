"""Pytest global test fixtures and configuration."""

import sys
from collections.abc import AsyncIterator
from pathlib import Path

# Add services and packages to sys.path for test discovery
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / "services" / "agent-x"))
sys.path.insert(0, str(root_dir / "packages" / "common"))

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from agentx.main import app  # noqa: E402


@pytest.fixture
async def async_client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

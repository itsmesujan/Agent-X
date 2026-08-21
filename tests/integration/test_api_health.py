"""Integration tests for API health and mission endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient) -> None:
    response = await async_client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_create_mission_endpoint(async_client: AsyncClient) -> None:
    payload = {
        "title": "Audit Security Posture",
        "goal_statement": "Audit Cloud Run IAM roles and produce remediation PR.",
        "max_usd_budget": 5.00,
        "max_runtime_minutes": 60,
    }
    response = await async_client.post(
        "/api/v1/missions",
        json=payload,
        headers={"Authorization": "Bearer dev-token-auditor"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "mission_id" in data
    assert data["title"] == payload["title"]

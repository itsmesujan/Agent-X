"""Integration tests for Goal Engine using real Gemini 2.5 Pro API."""

import os

import pytest

from agentx.goal_engine import GoalEngine, ParsedGoalOutput
from agentx.llm import GeminiLLMProvider


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="Requires GEMINI_API_KEY environment variable for live Gemini integration test",
)
def test_real_gemini_goal_deconstruction() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    provider = GeminiLLMProvider(api_key=api_key)
    engine = GoalEngine(llm_provider=provider)

    prompt = (
        "Scan our Google Cloud Storage buckets for public read permissions, "
        "enforce uniform bucket-level access via Terraform, and generate a compliance report."
    )

    result: ParsedGoalOutput = engine.deconstruct_goal(prompt)

    assert result.title != ""
    assert len(result.primary_objective) > 10
    assert len(result.deliverables) >= 1
    assert len(result.success_criteria) >= 1
    assert result.deadline_seconds > 0
    assert result.risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert len(result.required_capabilities) >= 1

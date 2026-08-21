"""Agent-X Pricing Matrix and Cost Calculation Math."""

from agentx.resource_brain.schemas import ModelTier

# Google Cloud Gemini API Pricing (USD per token)
PRICING_RATES: dict[ModelTier, dict[str, float]] = {
    ModelTier.GEMINI_2_5_FLASH: {
        "input_per_token": 0.075 / 1_000_000.0,
        "cached_per_token": 0.01875 / 1_000_000.0,
        "output_per_token": 0.30 / 1_000_000.0,
    },
    ModelTier.GEMINI_2_5_FLASH_THINKING: {
        "input_per_token": 0.075 / 1_000_000.0,
        "cached_per_token": 0.01875 / 1_000_000.0,
        "output_per_token": 0.30 / 1_000_000.0,
    },
    ModelTier.GEMINI_2_5_PRO: {
        "input_per_token": 1.25 / 1_000_000.0,
        "cached_per_token": 0.3125 / 1_000_000.0,
        "output_per_token": 5.00 / 1_000_000.0,
    },
    ModelTier.GEMINI_3_7_FLASH: {
        "input_per_token": 0.075 / 1_000_000.0,
        "cached_per_token": 0.01875 / 1_000_000.0,
        "output_per_token": 0.30 / 1_000_000.0,
    },
    ModelTier.GEMINI_3_1_PRO: {
        "input_per_token": 1.25 / 1_000_000.0,
        "cached_per_token": 0.3125 / 1_000_000.0,
        "output_per_token": 5.00 / 1_000_000.0,
    },
}


def calculate_llm_cost(
    model: ModelTier,
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
) -> float:
    """Calculate exact USD cost for a Gemini API invocation."""
    rates = PRICING_RATES.get(model, PRICING_RATES[ModelTier.GEMINI_2_5_FLASH])
    uncached_input = max(0, input_tokens - cached_tokens)

    cost = (
        uncached_input * rates["input_per_token"]
        + cached_tokens * rates["cached_per_token"]
        + output_tokens * rates["output_per_token"]
    )
    return round(cost, 6)

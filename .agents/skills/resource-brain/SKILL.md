---
name: resource-brain
description: Quantitatively governs token allocations, dollar costs, rate limits, timeouts, and dynamic model routing.
---

# Resource Brain Skill

## 1. Purpose
Enforce quantitative resource governance across Agent-X missions by managing token budgets, financial spend ceilings, API rate limits, execution timeouts, and intelligent Gemini model routing.

## 2. When to Use
- When sizing and budgeting new missions during the planning phase.
- When assigning per-task token allowances and timeout limits.
- When dynamically routing tasks between Gemini 2.5 Pro and Gemini 2.5 Flash.
- When monitoring active token consumption and enforcing hard stop circuit breakers.

## 3. Constraints
- Hard budget caps are inviolable: If cumulative spend hits $100\%$, the mission MUST pause immediately.
- Gemini 2.5 Flash must be used for routine sensory, regex, and syntactic tasks.
- Must track cached tokens vs non-cached tokens for accurate sub-cent billing.

## 4. Inputs
- Mission master budget parameters (`max_usd_limit`, `max_total_tokens`, `max_execution_time_seconds`).
- Task complexity scores and prompt token estimates.
- Real-time token consumption reports from subagent executions.

## 5. Outputs
- `TaskResourceAllocation` objects attached to task nodes.
- Real-time budget telemetry events streamed to Mission Control.
- Dynamic throttling directives and backpressure signals to Pub/Sub queues.

## 6. Implementation Rules
1. Calculate task complexity: $C = w_1 \cdot \text{ReasoningDepth} + w_2 \cdot \text{CodeSize} + w_3 \cdot \text{ToolCount}$.
2. Route to Flash if $C < 0.4$, route to Pro if $C \ge 0.4$.
3. Emit a warning at $80\%$ budget consumption; pause and alert at $100\%$.
4. Enforce exponential jitter backoff on HTTP 429 rate limit responses.

## 7. Testing Requirements
- Unit test cost estimation math against official Google Cloud pricing formulas.
- Test circuit breaker activation when simulated token usage crosses the ceiling.

## 8. Failure Conditions
- Runaway token consumption exceeding mission caps.
- Allocating Gemini Pro to trivial formatting tasks, wasting budget.

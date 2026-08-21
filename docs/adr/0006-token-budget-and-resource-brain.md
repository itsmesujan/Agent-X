# ADR 0006: Dynamic Token Budgeting & Resource Brain Governance

## Status
**Accepted**

## Context
Autonomous agents running in unconstrained loops risk financial runaways, quota exhaustion, and cascading API throttling. A mission with circular replanning or runaway retry loops can consume millions of tokens in minutes. We must enforce hard financial, computational, and rate boundaries.

## Decision
We implement the **Resource Brain** as a mandatory quantitative governor integrated into the Mission Coordinator and Cloud Run worker pools:
1. **Multi-Dimensional Budgeting**: Every mission specifies a hard cap on USD spend (default $5.00), total tokens (default 1,000,000), and execution duration (default 3,600s).
2. **Dynamic Task Allocations**: Tasks receive token ceilings based on their complexity rating and model tier.
3. **Automated Intercept & Safe Pause**: When spend reaches $80\%$, an alert is raised. At $100\%$, the mission transitions to `PAUSED (BUDGET_EXHAUSTED)`, requiring human quota expansion to resume.
4. **Intelligent Model Routing**: Routine sensory and parsing operations are routed to Gemini 2.5 Flash, preserving Gemini 2.5 Pro tokens for deep reasoning.

## Rationale
- **Predictable Operational Costs**: Guarantees that no mission can exceed its designated financial budget.
- **Fail-Safe Operation**: Prevents infinite recursion loops during complex replanning or error recovery.
- **Fair Resource Sharing**: Prevents a single rogue mission from consuming organization-wide Gemini API quotas.

## Consequences
- **Positive**: Strict financial predictability, prevention of runaway loops, cost optimization via model routing.
- **Negative**: Missions with complex goals and very tight budgets may pause prematurely if the initial budget estimate was too conservative, requiring operator intervention to add quota.

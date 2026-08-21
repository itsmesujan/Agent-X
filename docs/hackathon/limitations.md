# Hackathon Submission: Limitations & Boundary Analysis

To maintain absolute intellectual honesty and adhere to the Agent-X Engineering Constitution, we document the current operational boundaries of the system:

---

## 1. Known Operational Boundaries

1. **Destructive Execution Boundaries**:
   - Agent-X strictly mandates Human-in-the-Loop (HITL) approval for destructive infrastructure actions (e.g. `gcloud projects delete`, dropping production databases, force pushing Git branches).
2. **Deterministic Context Window Sizing**:
   - While Gemini 2.5 Pro supports up to 2M tokens of context, unbounded accumulation in single-turn prompts increases cost. The Resource Brain actively prunes and summarizes historical observations to stay within budget constraints.
3. **External Rate Limits**:
   - Tool operations that depend on third-party public web APIs (e.g., GitHub REST API, unauthenticated search endpoints) may encounter upstream HTTP 429 rate limits, which are handled via exponential backoff.

---

## 2. Security Boundaries

- Agent-X enforces execution sandboxing with dropped capabilities (`CAP_DROP_ALL`) and strictly whitelisted filesystem directories. Tasks requiring low-level kernel driver modifications or root access are prohibited by design.

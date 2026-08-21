---
name: product-requirements
description: Defines product scope, user stories, acceptance criteria, MVP boundaries, and KPIs for Agent-X.
---

# Product Requirements Skill

## 1. Purpose
Translate user objectives and high-level ideas into structured, unambiguous product requirements, user stories, verifiable acceptance criteria, and explicit non-goals.

## 2. When to Use
- When defining new user-facing features, mission types, or UI views.
- When deconstructing high-level objectives into the `GoalContract`.
- When scoping releases, MVP boundaries, and hackathon deliverables.
- When validating that planned features satisfy user needs without scope creep.

## 3. Constraints
- Must maintain strict separation between MVP (Phase 0), Enterprise Beta (Phase 1), and GA (Phase 2).
- Every requirement must have measurable, observable acceptance criteria.
- Never silently expand scope or accept vague definitions of done.

## 4. Inputs
- User input, feature requests, or business requirements.
- Existing `/docs/product-requirements.md` and `/docs/functional-requirements.md`.

## 5. Outputs
- Structured User Stories (`As a [persona], I want [capability] so that [benefit]`).
- Given-When-Then testable acceptance criteria.
- In-Scope vs Non-Goals boundary definitions.
- Feature specifications in `/docs/features/`.

## 6. Implementation Rules
1. Map every feature to one of the core personas: Mission Commander, Auditor/Reviewer, or System Admin.
2. Ensure every functional requirement specifies observable outputs (e.g. status code, database state, GCS artifact).
3. Explicitly state rate limits, latency budgets, and security constraints for every user flow.

## 7. Testing Requirements
- Review requirements for testability: If an acceptance criterion cannot be asserted by an automated test or auditor check, reject and refine it.

## 8. Failure Conditions
- Acceptance criteria written in subjective terms (e.g. "runs fast", "looks good").
- Unbounded feature creep that violates the Hackathon MVP timeline.

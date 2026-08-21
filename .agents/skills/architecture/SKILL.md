---
name: architecture
description: Guides system design, ADR generation, module boundaries, and architectural consistency across Agent-X.
---

# Architecture Skill

## 1. Purpose
Enforce architectural integrity across Agent-X, manage module boundaries, evaluate design trade-offs, author Architecture Decision Records (ADRs), and ensure strict alignment with `/docs/system-architecture.md` and related system specifications.

## 2. When to Use
- When introducing new system components, services, or cross-cutting boundaries.
- When evaluating structural trade-offs (e.g. database selections, messaging protocols, memory architectures).
- When documenting or modifying architectural decisions via ADRs in `/docs/adr/`.
- During architectural reviews and contradiction audits.

## 3. Constraints
- Must NOT silently change existing architecture or introduce unapproved external frameworks.
- Every architectural change MUST produce a numbered ADR in `/docs/adr/`.
- Must preserve the core closed-loop mission paradigm (`GOAL → WORLD MODEL → UNKNOWNS → PLAN → RESOURCE ALLOCATION → EXECUTE → OBSERVE → VERIFY → RECOVER → UPDATE → REPLAN → OUTCOME`).

## 4. Inputs
- Problem statements, scaling requirements, or feature specifications.
- Existing documentation in `/docs/` and `/docs/adr/`.
- System telemetry and benchmark performance profiles.

## 5. Outputs
- Numbered ADR markdown documents (`/docs/adr/XXXX-title.md`).
- Architectural diagrams (Mermaid format).
- Interface and module boundary definitions.
- Updates to `/docs/system-architecture.md` and `/docs/architecture-review.md`.

## 6. Implementation Rules
1. Follow the standard ADR structure: Status, Context, Decision, Rationale, Consequences.
2. Align all compute with Google Cloud Run, messaging with Pub/Sub, state with Firestore/GCS, and LLM reasoning with Google ADK + Gemini 2.5.
3. Decouple strategy (Coordinator/Architect) from tactic execution (Worker subagents).

## 7. Testing & Verification Requirements
- Verify that proposed designs introduce no circular module dependencies.
- Validate that all communication interfaces support asynchronous non-blocking I/O.
- Verify backward compatibility for existing Firestore document schemas.

## 8. Failure Conditions
- Proposing changes that violate zero-trust security or least-privilege IAM.
- Introducing unmanaged stateful servers instead of serverless Cloud Run / Firestore.
- Merging architectural updates without approved ADRs.

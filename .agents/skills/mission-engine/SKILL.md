---
name: mission-engine
description: Governs the end-to-end mission lifecycle, master state machine, goal deconstruction, and deliverable assembly.
---

# Mission Engine Skill

## 1. Purpose
Orchestrate the master mission lifecycle from initial goal formulation to final deliverable synthesis, enforcing the core Agent-X state machine and SLA invariants.

## 2. When to Use
- When initializing a new mission from user input (`POST /api/v1/missions`).
- When managing transitions across master states (`DRAFT`, `PARSING_GOAL`, `READY`, `EXECUTING`, `PAUSED`, `COMPLETED`, `FAILED`, `ABORTED`).
- When assembling the final outcome package and generating completion certificates.

## 3. Constraints
- The mission cannot transition to `COMPLETED` unless 100% of terminal DAG tasks are in `VERIFIED` status.
- State transitions must be atomic and recorded in Firestore.
- Must respect mission-level budgets (USD cap, token limit, timeout).

## 4. Inputs
- User goal statement, input files, constraints, and budget parameters.
- Real-time task completion signals and verification proofs.

## 5. Outputs
- Initialized Mission Document in Firestore.
- Mission lifecycle state events published to Pub/Sub.
- Final mission deliverable package (summary markdown, unified diff, GCS evidence archive).

## 6. Implementation Rules
1. Deconstruct user objectives into the structured `GoalContract` using Gemini 2.5 Pro.
2. Initialize master budget and assign default safety constraints ($5 USD default cap, 1 hr timeout).
3. If an unrecoverable error occurs in a critical path, transition mission to `FAILED` and preserve all artifacts for post-mortem debugging.
4. Support pause/resume semantics for Human-in-the-Loop (HITL) interactions.

## 7. Testing Requirements
- Test state machine transitions under valid and invalid inputs.
- Validate timeout watchdog behavior when a mission exceeds its SLA.

## 8. Failure Conditions
- Premature completion of missions with unverified tasks.
- Silent mission crashes that leave Firestore state in `EXECUTING` indefinitely.

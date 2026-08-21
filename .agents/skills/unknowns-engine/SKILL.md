---
name: unknowns-engine
description: Proactively discovers, categorizes, isolates, and resolves epistemic unknowns before destructive execution.
---

# Unknowns Engine Skill

## 1. Purpose
Identify knowledge gaps, missing parameters, undocumented APIs, untested assumptions, and permission ambiguities before mutating downstream state, generating high-priority exploratory tasks to resolve them.

## 2. When to Use
- During goal deconstruction and initial DAG planning.
- When an agent encounters an ambiguous error or missing input dependency.
- Before executing destructive, non-idempotent tasks (e.g. database migration, cloud deployment).

## 3. Constraints
- Destructive tasks MUST NOT execute while blocked by active `CRITICAL_UNKNOWN` entities.
- Exploratory tasks must be read-only and strictly bounded in token budget and execution time.

## 4. Inputs
- Goal specifications, repository trees, and tool parameter requirements.
- Entity graphs with missing attributes or low confidence scores.

## 5. Outputs
- `CRITICAL_UNKNOWN` entity nodes in the World Model.
- High-priority exploratory `TaskNode` objects inserted at the root of the DAG.
- Resolution events converting unknowns to `KNOWN_FACT` upon discovery.

## 6. Implementation Rules
1. Automatically scan task inputs for undefined variables, missing credentials, or unverified endpoints.
2. Formulate targeted discovery questions (e.g. "What is the schema of table `users`?", "Does the Cloud Run service have public ingress?").
3. Dispatch specialized discovery tools (e.g. `gcloud describe`, `curl -I`, `ls -la`, `git status`).

## 7. Testing Requirements
- Test that missing parameters correctly trigger exploratory tasks instead of crashing workers.
- Verify that resolving an unknown unlocks downstream tasks in the Workflow Engine.

## 8. Failure Conditions
- Silently guessing an unknown parameter value instead of discovering it.
- Generating open-ended, non-terminating discovery loops.

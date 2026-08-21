---
name: workflow-engine
description: Synthesizes, schedules, parallelizes, and dynamically mutates the Task DAG during mission execution.
---

# Workflow Engine Skill

## 1. Purpose
Manage the synthesis, topological sorting, parallel execution scheduling, and dynamic live surgery of the Task Directed Acyclic Graph (DAG) across Cloud Run workers.

## 2. When to Use
- When generating the initial Task DAG from user objectives.
- When resolving dependencies and scheduling ready tasks to Pub/Sub.
- When performing dynamic DAG mutations (injecting repair sub-graphs or pruning redundant branches).
- When validating DAG acyclicity and topological ordering.

## 3. Constraints
- The Task DAG must remain strictly acyclic (no circular dependencies).
- Tasks can only be dispatched when 100% of their upstream dependencies are in `VERIFIED` status.
- DAG mutations must be committed atomically via Firestore batched writes.

## 4. Inputs
- Goal contracts, subagent role definitions, and entity relationship graphs.
- Task status change events (`VERIFIED`, `FAILED`).
- Recovery directives requesting DAG mutations.

## 5. Outputs
- Topologically sorted list of `TaskNode` objects in Firestore.
- `TaskDispatchEvent` payloads published to Pub/Sub `agentx-task-dispatch`.
- DAG mutation audit logs recording injected or skipped nodes.

## 6. Implementation Rules
1. Implement Kahn's algorithm / DFS for topological sorting and cycle detection.
2. Calculate idempotency keys ($H = \text{SHA256}(\text{inputs} + \text{role} + \text{task\_id})$) to prevent duplicate execution.
3. When a task fails, pause all downstream dependent nodes before injecting repair subtrees.
4. Unlock parallel branches immediately as their prerequisite dependencies verify.

## 7. Testing Requirements
- Test DAG generator on complex dependency graphs (diamond dependencies, wide parallel trees).
- Assert that cycle detection correctly rejects invalid plans.
- Test live subtree injection during simulated task failure.

## 8. Failure Conditions
- Deadlocked workflows caused by unhandled dependency cycles.
- Dispatching a task before its upstream prerequisites have been verified.

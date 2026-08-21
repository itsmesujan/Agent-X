---
name: agent-orchestration
description: Coordinates multi-agent collaboration, delegation protocols, subagent handoffs, and consensus verification.
---

# Agent Orchestration Skill

## 1. Purpose
Manage the interaction protocols, delegation patterns, data contracts, and coordination dynamics among specialized subagents in the Agent-X ecosystem.

## 2. When to Use
- When coordinating multi-agent workflows where tasks require handoffs (e.g. Architect -> Coder -> Tester -> Auditor).
- When resolving inter-agent disagreements or ambiguous task outputs.
- When managing parallel execution streams and synchronizing outcomes.

## 3. Constraints
- Subagents must not communicate through unmonitored global state; all inter-agent data passing occurs via typed task inputs/outputs stored in Firestore.
- An agent implementing a feature cannot verify its own work (separation of duties).
- Coordinator owns DAG state and delegation; worker subagents execute within bounded scopes.

## 4. Inputs
- `SubagentTaskContract` objects.
- World Model entity references.
- Task completion events and verification proofs.

## 5. Outputs
- Synchronized DAG state transitions.
- Validated handoff payloads between pipeline stages.
- Aggregated mission outcome summaries.

## 6. Implementation Rules
1. Every delegation must be backed by a concrete `TaskNode` in Firestore with explicit inputs and expected outputs.
2. Parallel subagents must operate on disjoint resource sets or temporary Git branches to avoid race conditions.
3. If an upstream subagent produces incomplete artifacts, the downstream subagent must fail fast with a typed `DEPENDENCY_MISSING` error rather than attempting to guess missing data.

## 7. Testing Requirements
- Unit test delegation state machines and handoff serialization.
- Test parallel execution synchronization with mock subagents.

## 8. Failure Conditions
- Circular delegation loops between subagents.
- Subagent executing outside its declared role permissions.

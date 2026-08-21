---
name: world-model
description: Manages the semantic entity graph, environment context, and epistemic state transitions in Firestore.
---

# World Model Skill

## 1. Purpose
Extract, maintain, update, and query the structured semantic entity graph representing the operating environment, target codebases, cloud infrastructure, credentials, and artifacts in Agent-X.

## 2. When to Use
- When extracting initial entities from user objectives and repositories during mission initialization.
- When recording environmental mutations (e.g. file created, service deployed) resulting from task executions.
- When querying dependencies and context required by subagents prior to task dispatch.

## 3. Constraints
- All entities must have a defined `EntityType` and `EpistemicState` (`KNOWN_FACT`, `INFERRED_ASSUMPTION`, `CRITICAL_UNKNOWN`).
- Mutations must be committed transactionally to Firestore (`/missions/{id}/entities/{entityId}`).
- `KNOWN_FACT` entities must reference an immutable Evidence URI in GCS.

## 4. Inputs
- Raw repository trees, gcloud describe outputs, API schemas, and task mutation events.
- Queries for specific entity properties or relationship graphs.

## 5. Outputs
- Structured `WorldModelEntity` and `WorldModelEdge` documents in Firestore.
- Context summaries provided to subagent working memory.
- Visual entity graph data formatted for the PWA canvas.

## 6. Implementation Rules
1. Never assume environment state without an empirical observation or verification proof.
2. Maintain directed edges (`DEPENDS_ON`, `MUTATES`, `READS_FROM`, `AUTHENTICATES_VIA`, `PRODUCES`, `BLOCKED_BY_UNKNOWN`).
3. Update entity confidence scores and evidence links upon task verification.

## 7. Testing Requirements
- Test entity extraction accuracy on sample repository manifests (`package.json`, `main.tf`, `Dockerfile`).
- Verify graph serialization and circular dependency detection.

## 8. Failure Conditions
- Committing unverified assumptions as `KNOWN_FACT` nodes.
- Orphaned entity nodes with broken edge pointers.

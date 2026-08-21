---
name: firestore
description: Manages Firestore Native Mode collections, real-time snapshot listeners, transactions, and security rules.
---

# Google Cloud Firestore Skill

## 1. Purpose
Design, implement, query, and secure Google Cloud Firestore in Native Mode for Agent-X, supporting real-time mission synchronization, atomic task locking, hierarchical subcollections, and composite indexing.

## 2. When to Use
- When reading or writing missions, tasks, entities, edges, proofs, or checkpoints.
- When configuring real-time snapshot listeners (`on_snapshot` in Python, `onSnapshot` in JS).
- When implementing atomic transactions (e.g. task claiming and state locking).
- When writing composite index configurations (`firestore.indexes.json`) and security rules (`firestore.rules`).

## 3. Constraints
- Use Native Mode (not Datastore mode).
- Keep document sizes strictly under 1 MB (offload large logs and artifacts to Cloud Storage).
- Prevent partition hotspots by sharding high-frequency logs across mission subcollections (`/missions/{id}/logs`).

## 4. Inputs
- Mission state mutations, task status transitions, and entity graph updates.
- Query filters (e.g. all `READY` tasks for a mission).

## 5. Outputs
- Firestore documents and subcollection structures.
- Atomic batch write commits and transaction locks.
- `firestore.indexes.json` and `firestore.rules` configuration files.

## 6. Implementation Rules
1. Implement atomic transactions for task status transitions to prevent duplicate worker execution.
2. Use batched writes (`write_batch`) when committing multiple DAG nodes or entity updates simultaneously.
3. Structure subcollections under `/missions/{missionId}/`: `/tasks`, `/entities`, `/edges`, `/proofs`, `/logs`, `/checkpoints`.
4. Ensure all timestamp fields use UTC Firestore timestamps (`SERVER_TIMESTAMP`).

## 7. Testing Requirements
- Test all database queries against the local **Google Cloud Firestore Emulator**.
- Verify that transactional locks reject concurrent worker race conditions.

## 8. Failure Conditions
- Exceeding document size limits by storing raw code repositories directly in Firestore.
- Unindexed queries that cause runtime collection scan errors.

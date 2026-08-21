# Agent-X Architecture Review & Contradiction Audit

## 1. Executive Summary

This architecture review performs a critical, end-to-end evaluation of the **Agent-X Autonomous Mission Operating System** specification. It analyzes alignment across all 20 specification documents and 6 Architecture Decision Records (ADRs), identifying subtle contradictions, missing requirements, technical and cost risks, security boundaries, and actionable architectural remedies.

---

## 2. Contradiction & Alignment Audit

| ID | Issue Identified | Affected Documents | Analysis & Root Cause | Recommended Harmonization / Fix |
| :--- | :--- | :--- | :--- | :--- |
| **CA-01** | **Pub/Sub Task Ingestion Mechanism** | `cloud.md`, `system-architecture.md`, `ADR 0003` | `cloud.md` defines a Pub/Sub *Push* subscription to Cloud Run (`/api/v1/tasks/process`), whereas `agent-architecture.md` and `system-architecture.md` intermittently refer to workers "pulling" tasks. Push subscriptions are bounded by HTTP request timeouts and require Cloud Run to expose an internal HTTPS endpoint with OIDC auth. | Standardize strictly on **Pub/Sub Push Subscription with OIDC Authentication** to Cloud Run Worker service. Configure Cloud Run request timeout to $600\text{ s}$ and Pub/Sub Ack Deadline to $300\text{ s}$ with automated lease renewal via background heartbeats. |
| **CA-02** | **Real-Time Data Streaming Topology** | `database.md`, `api.md`, `frontend.md` | `database.md` mentions direct Firestore client SDK snapshot listeners for UI updates, while `api.md` defines SSE endpoints (`/telemetry/stream`) and WebSockets (`/terminal/ws`). Without a clear separation of concerns, the frontend could open redundant connections. | Explicitly define the **Tri-Channel Streaming Model**: <br/>1. **Firestore Client Listeners**: For low-frequency, strongly consistent Mission and Task DAG state changes (`missions/{id}/tasks`).<br/>2. **FastAPI SSE (`/telemetry/stream`)**: For high-frequency read-only agent thought traces, log streams, and token counters.<br/>3. **FastAPI WebSocket (`/terminal/ws`)**: Reserved exclusively for interactive HITL terminal sessions requiring bidirectional stdin/stdout. |
| **CA-03** | **Task Idempotency vs Pub/Sub At-Least-Once Delivery** | `workflow-engine.md`, `database.md` | Pub/Sub guarantees at-least-once delivery. If two worker instances receive duplicate task messages simultaneously, both could execute destructive tools. | Implement a **Firestore Transactional Task Lock**: Before a worker begins tool execution, it must execute a Firestore atomic transaction to transition task status from `READY` to `DISPATCHED/RUNNING` and record `locked_by_worker_id`. If the lock is already claimed, the duplicate message is acknowledged and discarded. |

---

## 3. Missing Requirements & Gap Analysis

1. **MR-01: Multi-Task Artifact Aggregation Protocol**:
   - *Gap*: When multiple parallel tasks produce separate artifacts (e.g. Task 3 modifies Python backend code, Task 4 writes Terraform infra, Task 5 creates docs), the system lacks an explicit specification for how these are merged into a single atomic Git commit or deliverable archive.
   - *Fix*: Introduce an automated **Synthesizer / Merge Task Node** at the convergence point of parallel DAG branches, responsible for resolving merge conflicts and creating a unified PR.
2. **MR-02: Long-Running Task Heartbeat & Lease Extension**:
   - *Gap*: If a task takes 4 minutes to run tests, a Pub/Sub push request with an ack deadline of 300s might be close to timing out or redelivering if network spikes occur.
   - *Fix*: Implement an automated background task heartbeat in the worker that periodically updates the task's `last_heartbeat_at` in Firestore and issues Pub/Sub lease extension calls if pull subscriptions are used, or ensures HTTP keepalive on push connections.
3. **MR-03: Firestore Security Rules Definition**:
   - *Gap*: The database specification details document schemas and indexes, but omits the declarative Firestore Security Rules required for secure client-side PWA reads.
   - *Fix*: Provide explicit `firestore.rules` allowing read access to authenticated mission collaborators while restricting writes strictly to backend service accounts.

---

## 4. Risk Assessment & Mitigations

### 4.1 Technical Risks
- **Risk TR-01: Cloud Run Cold Starts**: Workers scaling from 0 to 50 under sudden DAG parallelism may experience 2.5–4.0s cold starts.
  - *Mitigation*: Configure minimum instance of 1 for the worker pool in staging/production, and utilize lightweight Alpine/Distroless container images with pre-warmed Python virtual environments.
- **Risk TR-02: Complex State Re-synchronization on PWA Disconnect**: Network loss on mobile/desktop PWA could lead to stale DAG states in React Flow.
  - *Mitigation*: TanStack Query and Firestore client SDK handle automatic local cache invalidation and snapshot reconciliation upon network reconnection.

### 4.2 Cost Risks
- **Risk CR-01: Runaway LLM Costs during Recursive Replanning**: Complex tasks encountering repeated failures could consume millions of tokens in minutes.
  - *Mitigation*: Hard budget ceiling enforced by the Resource Brain. Maximum 3 automated replan iterations per mission branch before mandatory HITL escalation.

### 4.3 Security Risks
- **Risk SR-01: Remote Code Execution & Container Escape**: Untrusted code executed by Coder/Tester subagents could attempt privilege escalation or access the GCP metadata server.
  - *Mitigation*: Disable GCP metadata server access on the worker container via iptables/Cloud Run network configuration; run worker processes as non-root user `UID 1001` with `CAP_DROP_ALL`.
- **Risk SR-02: Secret Leakage in Logs**: Sensitive API keys and access tokens returned by tools could leak into the public telemetry stream.
  - *Mitigation*: Mandatory regex and entropy-based token redaction filter executed in-memory before writing to Firestore or emitting SSE log events.

### 4.4 Implementation & Operational Risks
- **Risk IR-01: Google ADK API Version Evolution**: The Google Gen AI SDK and Agent Development Kit are under active development and may introduce interface changes.
  - *Mitigation*: Abstract all ADK agent invocations behind internal `AgentRunnerInterface` adapters, isolating core workflow and state machine logic from SDK signature updates.

---

## 5. Recommended Fixes & Next Steps

1. **Deploy GCP Emulators First**: In development, run the complete workflow engine against Firestore and Pub/Sub emulators to validate state machine transitions and locking without cloud costs.
2. **Implement Typed Verification Proofs**: Ensure the Level 1–4 Verification protocol is treated as a hard gate with machine-readable JUnit XML parsing and SHA-256 integrity verification.
3. **Create `firestore.rules` & `firestore.indexes.json`**: Integrate declarative security and indexing into the Terraform pipeline before deploying Cloud Run services.
4. **Final Verdict**: The Agent-X architecture is robust, highly modular, cloud-native, and strategically sound. Proceed to Phase 0 implementation upon review approval.

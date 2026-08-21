# Agent-X Non-Functional Requirements (NFR)

## 1. Performance & Latency Budgets

| Metric | Target SLA | 95th Percentile | Measurement Method |
| :--- | :--- | :--- | :--- |
| **API Response Time (CRUD)** | $< 150\text{ ms}$ | $< 300\text{ ms}$ | Cloud Monitoring / HTTP traces |
| **DAG Generation (Gemini 2.5 Pro)** | $< 6.0\text{ s}$ | $< 10.0\text{ s}$ | Backend task dispatch span |
| **Realtime Telemetry Latency** | $< 200\text{ ms}$ | $< 500\text{ ms}$ | Pub/Sub to Firestore to Web UI SSE |
| **Worker Cold Start (Cloud Run)** | $< 2.5\text{ s}$ | $< 4.0\text{ s}$ | Cloud Run container launch logs |
| **Evidence Verification Check** | $< 1.5\text{ s}$ | $< 3.0\text{ s}$ | Verifier pipeline execution duration |
| **PWA Initial Load (FCP / LCP)** | $< 1.2\text{ s}$ | $< 2.0\text{ s}$ | Chrome Lighthouse / Core Web Vitals |

---

## 2. Scalability & Concurrency

- **Horizontal Worker Auto-Scaling**: Cloud Run backend and worker pools must scale from 0 to 100+ concurrent worker instances dynamically under Pub/Sub load spikes.
- **Concurrent Missions**: Support up to 50 concurrent active multi-agent missions per project tenant without database write lock contention.
- **Firestore Throughput**: Data model must shard high-frequency logging across mission-scoped subcollections (`missions/{missionId}/logs`) to prevent exceeding Firestore's 10,000 writes/sec partition limits.
- **Queue Buffering**: Pub/Sub topic architecture must handle bursts of up to 1,000 task events/sec without message drop, supported by dedicated Dead Letter Queues (DLQ).

---

## 3. Reliability, Availability & Fault Tolerance

- **System Availability Target**: $99.9\%$ uptime for Mission Control API and state engine.
- **Zero State Loss (Crash Consistency)**: All task state mutations, evidence hashes, and world model entities must be committed to Firestore before transitioning task status to `COMPLETED` or `FAILED`.
- **Worker Crash Resilience**: If a Cloud Run worker terminates mid-task (OOM, preemption, timeout), the unacknowledged Pub/Sub message will be redelivered after the ack deadline (default: 300s) to a healthy worker instance with idempotency checks.
- **Circuit Breakers**: External API integrations (e.g. GitHub API, Gemini API, external bash runners) must implement exponential backoff with jitter and circuit breakers to avoid cascading resource exhaustion during third-party outages.

---

## 4. Security & Isolation

- **Zero Trust Cloud Runtime**:
  - Principle of Least Privilege: Every Cloud Run service account is restricted via IAM roles (`roles/firestore.dataEditor`, `roles/pubsub.publisher`, etc.).
  - Workload Identity Federation for external integrations.
- **Secret Management**:
  - Zero hardcoded credentials. All LLM API keys, Git credentials, and third-party tokens are loaded dynamically from Google Secret Manager at runtime.
  - Automatic redaction of API keys, bearer tokens, and passwords in all logs streamed to Firestore or UI.
- **Sandboxed Execution**:
  - Worker bash and code evaluation must execute inside unprivileged, ephemeral container environments with filesystem isolation and network egress filtering where required.
- **Data Protection & Encryption**:
  - All data at rest encrypted using Google Default Encryption or Customer-Managed Encryption Keys (CMEK).
  - All data in transit strictly enforced over TLS 1.3.

---

## 5. Observability & Telemetry

- **Distributed Tracing**: OpenTelemetry instrumentation integrated across FastAPI backend, Google ADK subagents, and Pub/Sub handlers, exported to Google Cloud Trace.
- **Structured Logging**: JSON-formatted structured logging matching Google Cloud Logging format with trace and span IDs injected.
- **Auditability**: Immutable audit trail of every user action, agent tool invocation, parameter payload, model response, and verification check stored in Cloud Storage and indexed in Firestore.

---

## 6. Maintainability & Code Quality

- **Type Safety**:
  - Frontend: 100% strict TypeScript (`noImplicitAny: true`, strict null checks).
  - Backend: 100% Python typing verified via `mypy` and Pydantic v2 schemas.
- **Test Coverage**: Minimum 85% line coverage on core business logic, workflow engine, state transitions, and verification engine.
- **Infrastructure as Code (IaC)**: 100% of GCP resources (Cloud Run, Pub/Sub, Firestore, Storage, Secret Manager, Cloud Armor, IAM) managed via modular, declarative Terraform configurations.

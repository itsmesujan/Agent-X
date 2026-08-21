# Hackathon Submission: Google Cloud Technology Integration

Agent-X is built from the ground up to showcase the full power, security, and scalability of **Google Cloud Platform (GCP)** and the **Google Gen AI / Gemini Ecosystem**:

---

## 1. Gemini Models & Google Gen AI SDK
- **Gemini 2.5 Pro & Frontier Models**: Used for high-complexity architectural planning, multi-source conflict reconciliation, and adversarial output verification.
- **Gemini 2.5 Flash & 3.7 Flash**: High-speed, cost-efficient execution engine for data analysis, web research, document parsing, and intermediate subagent workflows.
- **Gemini 2.5 Flash Thinking**: Multi-step chain-of-thought analysis for complex mathematical evaluations and root-cause failure classification.
- **Google Gen AI SDK (`google-genai`)**: Utilizes structured Pydantic schema generation, streaming completions, and safety settings.

---

## 2. Google Agent Development Kit (ADK) & Agent Runtime
- **Specialized Agent Hierarchy**: Implements role-segregated subagents (`PlannerAgent`, `ResearcherAgent`, `CoderAgent`, `VerifierAgent`, `RecoveryAgent`, `ArtifactAgent`) adhering to ADK design patterns.
- **Sandboxed Tool Registry**: Integrates secure tools with permission checks, rate limiting, and execution timeouts.

---

## 3. Serverless Compute: Google Cloud Run v2
- **`agent-x-api`**: FastAPI API Coordinator with auto-scaling to zero (`0` to `50` instances), WebSocket terminal streaming, and SSE event broadcast.
- **`agent-x-worker`**: Unprivileged Linux execution containers with 15-minute timeout windows for intensive subagent tasks.

---

## 4. Real-time Event Mesh: Google Cloud Pub/Sub
- **Decoupled Topics**: Asynchronously dispatches tasks (`agentx-task-events`), streams operational telemetry (`agentx-mission-events`), and handles self-healing events (`agentx-recovery-events`).
- **Dead-Letter Queue (DLQ)**: Automatic routing of poisoned or failing messages after 5 delivery retries for audit inspection.

---

## 5. Persistence: Google Cloud Firestore (Native Mode)
- **Document Model**: Stores missions, task DAGs, event histories, claim corroboration graphs, and World Model entities.
- **Optimistic Concurrency & PITR**: Point-in-time recovery and snapshot replication for high enterprise availability.

---

## 6. Immutable Storage: Google Cloud Storage (GCS)
- **Evidence Ledgers**: Secure buckets with uniform bucket-level access and object versioning for storing Level 1–4 cryptographic SHA-256 verification proofs and deliverable artifacts.
- **Lifecycle Archival**: Automatic transition of cold artifacts to `NEARLINE` storage.

---

## 7. Security & Observability
- **Google Secret Manager**: Zero hardcoded credentials; dynamic retrieval and in-memory TTL caching.
- **Cloud Logging & Cloud Monitoring**: Log-based metrics (`agentx_task_failures`, `agentx_security_rejections`), 5xx alert policies, and operational dashboards.

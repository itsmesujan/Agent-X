# Agent-X Database & Storage Schema Specification

## 1. Storage Paradigm

Agent-X adopts a dual-persistence strategy:
1. **Google Cloud Firestore (Native Mode)**: Strongly consistent document database for real-time state, missions, task DAGs, entity graphs, and live UI subscriptions.
2. **Google Cloud Storage (GCS)**: Scalable, immutable object store for raw execution logs, large tool outputs, code patches, screenshots, and cryptographic evidence.

---

## 2. Firestore Document Hierarchy

```text
/missions/{missionId}                                [Mission Master Document]
├── /tasks/{taskId}                                  [Task DAG Node Subcollection]
├── /entities/{entityId}                             [World Model Entity Subcollection]
├── /edges/{edgeId}                                  [World Model Graph Edges Subcollection]
├── /proofs/{proofId}                                [Evidence Verification Proofs]
├── /logs/{logId}                                    [Structured Telemetry & Output Logs]
└── /checkpoints/{checkpointId}                      [State & Rollback Checkpoints]

/evaluation_benchmarks/{benchmarkId}                 [Evaluation Benchmark Definitions]
└── /runs/{runId}                                    [Automated Benchmark Execution Runs]
```

---

## 3. Detailed Document Schemas

### 3.1 `/missions/{missionId}`
```json
{
  "mission_id": "msn_01HV8G7N2M0QY4T5P6Z8X1",
  "title": "Remediate Cloud Run Security & CI",
  "goal_statement": "Audit GCP security posture, fix IAM violations, and verify CI tests pass.",
  "status": "EXECUTING", // DRAFT | PARSING_GOAL | READY | EXECUTING | PAUSED | COMPLETED | FAILED | ABORTED
  "creator_id": "user_2aX9...",
  "budget": {
    "max_usd_limit": 10.00,
    "current_usd_spent": 1.42,
    "max_total_tokens": 1000000,
    "current_tokens_used": 142500,
    "max_execution_time_seconds": 3600
  },
  "metrics": {
    "total_tasks": 8,
    "completed_tasks": 3,
    "failed_tasks": 0,
    "running_tasks": 2
  },
  "created_at": "2026-08-21T10:00:00Z",
  "updated_at": "2026-08-21T10:15:30Z",
  "completed_at": null
}
```

### 3.2 `/missions/{missionId}/tasks/{taskId}`
```json
{
  "task_id": "task-01",
  "mission_id": "msn_01HV8G7N2M0QY4T5P6Z8X1",
  "name": "Audit IAM Service Account Permissions",
  "agent_role": "SECURITY_ANALYST",
  "status": "VERIFIED", // PENDING | READY | DISPATCHED | RUNNING | VERIFYING | VERIFIED | FAILED
  "dependencies": [],
  "dependent_children": ["task-03", "task-04"],
  "inputs": {
    "project_id": "agent-x-prod",
    "service_account": "sa-api@agent-x-prod.iam.gserviceaccount.com"
  },
  "outputs": {
    "violations_found": 2,
    "report_uri": "gs://agentx-evidence/missions/msn_.../tasks/task-01/report.json"
  },
  "idempotency_key": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "retry_count": 0,
  "max_retries": 3,
  "evidence_uri": "gs://agentx-evidence/missions/msn_.../tasks/task-01/verification_proof.json",
  "started_at": "2026-08-21T10:01:00Z",
  "completed_at": "2026-08-21T10:03:15Z"
}
```

### 3.3 `/missions/{missionId}/entities/{entityId}`
```json
{
  "entity_id": "entity_cloudrun_api",
  "mission_id": "msn_01HV8G7N2M0QY4T5P6Z8X1",
  "entity_type": "CLOUD_SERVICE",
  "name": "agent-x-api",
  "epistemic_state": "KNOWN_FACT", // KNOWN_FACT | INFERRED_ASSUMPTION | CRITICAL_UNKNOWN
  "confidence": 1.0,
  "properties": {
    "region": "us-central1",
    "ingress": "all",
    "current_image": "gcr.io/agent-x-prod/api:v1.2.0"
  },
  "evidence_uri": "gs://agentx-evidence/missions/msn_.../tasks/task-01/gcloud_describe.json",
  "updated_at": "2026-08-21T10:02:40Z"
}
```

---

## 4. Firestore Composite Indexes

To support efficient queries from the API and PWA, the following composite indexes are configured via `firestore.indexes.json`:

```json
{
  "indexes": [
    {
      "collectionGroup": "tasks",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "mission_id", "order": "ASCENDING" },
        { "fieldPath": "status", "order": "ASCENDING" },
        { "fieldPath": "started_at", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "logs",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "mission_id", "order": "ASCENDING" },
        { "fieldPath": "timestamp", "order": "ASCENDING" }
      ]
    }
  ]
}
```

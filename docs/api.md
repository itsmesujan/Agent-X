# Agent-X API Specification (REST, SSE & WebSockets)

## 1. Overview & Base Protocol

The Agent-X API is built with **FastAPI** (Python 3.12) adhering to OpenAPI 3.1 standards. It provides synchronous REST endpoints for mission management, Server-Sent Events (SSE) for telemetry streaming, and WebSockets for bidirectional interactive sessions.

- **Base URL**: `https://api.agentx.internal/api/v1`
- **Authentication**: `Authorization: Bearer <ID_TOKEN>` (Google Cloud Identity / Firebase Auth JWT)
- **Content-Type**: `application/json`

---

## 2. Mission Endpoints

### 2.1 Create / Formulate Mission
- **Endpoint**: `POST /missions`
- **Description**: Initializes a new mission from an open-ended goal, triggers initial Gemini 2.5 Pro planning, and populates the task DAG and World Model.
- **Request Body**:
  ```json
  {
    "title": "Migrate Database to Cloud SQL",
    "goal_statement": "Audit current SQLite database, generate PostgreSQL schema migration, deploy via Terraform, and verify data consistency.",
    "constraints": {
      "max_usd_budget": 15.00,
      "max_runtime_minutes": 60,
      "require_hitl_before_apply": true
    },
    "initial_context": {
      "git_repo": "https://github.com/org/sample-app",
      "target_environment": "staging"
    }
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "mission_id": "msn_01HV8G7N2M0QY4T5P6Z8X1",
    "status": "PARSING_GOAL",
    "created_at": "2026-08-21T10:00:00Z"
  }
  ```

---

### 2.2 Get Mission Details
- **Endpoint**: `GET /missions/{missionId}`
- **Response (200 OK)**:
  ```json
  {
    "mission_id": "msn_01HV8G7N2M0QY4T5P6Z8X1",
    "title": "Migrate Database to Cloud SQL",
    "status": "EXECUTING",
    "budget": {
      "max_usd_limit": 15.00,
      "current_usd_spent": 2.10,
      "max_total_tokens": 1000000,
      "current_tokens_used": 180400
    },
    "summary": {
      "total_tasks": 6,
      "verified_tasks": 2,
      "running_tasks": 1,
      "failed_tasks": 0
    }
  }
  ```

---

### 2.3 List Tasks in Mission DAG
- **Endpoint**: `GET /missions/{missionId}/tasks`
- **Response (200 OK)**:
  ```json
  {
    "tasks": [
      {
        "task_id": "task-01",
        "name": "Audit SQLite Schema",
        "agent_role": "ARCHITECT",
        "status": "VERIFIED",
        "dependencies": [],
        "evidence_uri": "gs://agentx-evidence/missions/msn_.../task-01/proof.json"
      },
      {
        "task_id": "task-02",
        "name": "Generate PostgreSQL DDL",
        "agent_role": "CODER",
        "status": "RUNNING",
        "dependencies": ["task-01"],
        "evidence_uri": null
      }
    ]
  }
  ```

---

### 2.4 Control Mission State (Pause / Resume / Abort)
- **Endpoint**: `POST /missions/{missionId}/actions`
- **Request Body**:
  ```json
  {
    "action": "PAUSE", // "PAUSE" | "RESUME" | "ABORT" | "FORCE_REPLAN"
    "reason": "Operator requested parameter adjustment."
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "mission_id": "msn_01HV8G7N2M0QY4T5P6Z8X1",
    "status": "PAUSED",
    "acknowledged_at": "2026-08-21T10:18:00Z"
  }
  ```

---

### 2.5 Submit HITL Decision / Input
- **Endpoint**: `POST /approvals/{approvalId}/approve` & `POST /approvals/{approvalId}/reject`
- **Request Body**:
  ```json
  {
    "operator_notes": "Approved for staging deployment."
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "status": "APPROVED",
    "approval_id": "appr_01HV8K9...",
    "updated_at": "2026-08-21T10:18:00Z"
  }
  ```

---

## 3. Dedicated Inspection & Subsystem Endpoints

### 3.1 Resource Monitor & Causal Allocation History
- **Endpoint**: `GET /missions/{missionId}/resource-monitor`
- **Description**: Returns 6-dimensional resource utilization tuples (`allocated`, `consumed`, `remaining`, `reserved`) for budget, time, compute, API usage, agent capacity, and tool locks, alongside a causal "WHY" change history timeline.
- **Reallocate Endpoint**: `POST /missions/{missionId}/resource-monitor/reallocate`

---

### 3.2 Evidence Explorer & Claim Verification
- **Endpoint**: `GET /missions/{missionId}/evidence-explorer`
- **Description**: Returns verified, refuted, or unverified claims, confidence scores, supporting/conflicting sources, and cryptographic Level 1–4 verification proofs.
- **Claim Detail Endpoint**: `GET /missions/{missionId}/evidence-explorer/claims/{claim_id}`

---

### 3.3 Failure Center & Chronological Mission Timeline
- **Endpoint**: `GET /missions/{missionId}/failures`
- **Description**: Returns failure records with 7 core attributes (failure, classification across 9 failure categories, affected task, recovery strategy across 9 self-healing strategies, replacement, additional resources, and result) plus the unified chronological mission timeline.

---

### 3.4 Artifact Center & Deliverable Management
- **Endpoints**:
  - `GET /missions/{missionId}/artifacts?category={REPORT|DATASET|PRESENTATION|SUMMARY|EVIDENCE_PACKAGE}`
  - `POST /missions/{missionId}/artifacts`
  - `GET /missions/{missionId}/artifacts/{artifactId}`
  - `GET /missions/{missionId}/artifacts/{artifactId}/download`
- **Description**: Manages categorized deliverable assets with SHA-256 integrity proofs, generation status, verification status, and direct browser download actions.

---

## 4. Realtime Streaming Endpoints

### 4.1 Server-Sent Events (SSE) Telemetry Stream
- **Endpoint**: `GET /missions/{missionId}/events`
- **Headers**: `Accept: text/event-stream`

---

### 4.2 Bidirectional WebSocket Terminal Console
- **Endpoint**: `WS /missions/{missionId}/terminal/ws`


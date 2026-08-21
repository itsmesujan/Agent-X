# Hackathon Submission: 3-Minute Demonstration Script

**Video Title**: *Agent-X: The Autonomous Mission Operating System with Gemini 2.5 & Google Cloud*  
**Presenter**: Mission Commander / Lead Architect  
**Duration**: 3 Minutes (180 Seconds)

---

## 🎬 Video Timeline & Screen Flow

### [00:00 – 00:30] Act 1: The Problem & The Mission Launch
- **Visual**: Open Mission Control PWA Dashboard (`/`). Show real-time fleet overview.
- **Narrator**:
  > *"Every engineer has watched an AI agent fail: burning through hundreds of dollars in API credits, getting trapped in infinite error loops, or hallucinating that a task succeeded when nothing was built. This is Agent-X — an enterprise-grade Autonomous Mission Operating System powered by Gemini 2.5 and Google Cloud."*
- **Action**: Click `New Mission` (`/missions/new`). Enter:
  - **Goal**: *"Audit legacy SQLite schema, generate PostgreSQL migration DDL with indexes, evaluate performance benchmarks, verify cryptographic evidence, and package deliverables."*
  - **Budget Cap**: `$5.00` | **Token Cap**: `1,000,000` | **Model Preference**: `Auto-Tiering (Flash/Pro)`.
- **Action**: Click **Launch Mission**.

---

### [00:30 – 01:15] Act 2: Dynamic DAG, World Model & Resource Brain
- **Visual**: Switch to **Mission Graph** (`/missions/[id]/graph`). Show React Flow DAG building in real-time.
- **Narrator**:
  > *"Instead of a fragile prompt chain, Agent-X constructs an operational Directed Acyclic Graph. Watch the Resource Brain in action: routine schema ingestion is dynamically routed to Gemini 2.5 Flash at 1/15th the cost. When complex DDL synthesis begins, the engine seamlessly routes to Gemini 2.5 Pro."*
- **Visual**: Navigate to **Resource Monitor** (`/missions/[id]/resources`). Show the 6-dimensional resource utilization tuple and the causal "WHY" change timeline.
- **Narrator**:
  > *"Every resource change is explainable — showing exactly why budget was reserved or reallocated."*

---

### [01:15 – 02:00] Act 3: Failure Injection & Autonomous Self-Healing
- **Visual**: Navigate to **Failure Center** (`/missions/[id]/failures`).
- **Action**: A simulated tool timeout / transient error triggers during benchmark execution.
- **Narrator**:
  > *"Notice what happens when a tool execution fails. Agent-X does not crash or swallow the error. The Recovery Engine classifies the error into 1 of 9 categories, selects the optimal self-healing strategy — in this case, swapping to an alternative data analysis tool with a 2-second backoff — and mutates the running workflow. The task turns green, completely self-healed."*
- **Visual**: Show the Chronological Mission Timeline capturing the self-healing event.

---

### [02:00 – 02:40] Act 4: Evidence Verification & Artifact Center
- **Visual**: Switch to **Evidence Explorer** (`/missions/[id]/evidence`).
- **Narrator**:
  > *"How do we know the agent didn't hallucinate? Every claim is backed by Level 1 through 4 Evidence Verification. We inspect supporting and conflicting sources, corroboration confidence scores, and cryptographic SHA-256 hashes."*
- **Visual**: Switch to **Artifact Center** (`/missions/[id]/artifacts`). Open the generated Migration Report and SQL DDL deliverable. Click **Download**.
- **Narrator**:
  > *"Real deliverables. Real files. Cryptographically verified in Google Cloud Storage."*

---

### [02:40 – 03:00] Act 5: Conclusion & Architecture
- **Visual**: Show the architecture diagram (Cloud Run v2, Firestore Native, Pub/Sub, Secret Manager, Terraform).
- **Narrator**:
  > *"100% cloud-native on Google Cloud, 100% verified with over 160 automated tests, and Zero Mock in production flows. Agent-X is the future of deterministic, resource-bounded autonomous engineering."*

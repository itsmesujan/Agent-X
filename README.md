# Agent-X: Autonomous Mission Operating System

Agent-X is an enterprise-grade autonomous mission operating system powered by Gemini 2.5 and the Google Agent Development Kit (ADK). It transforms open-ended user objectives into a structured, self-healing, resource-bounded, and verifiably proven operational Directed Acyclic Graph (DAG).

---

## 🚀 Core Closed-Loop Paradigm

```text
GOAL
 ↓
WORLD MODEL
 ↓
UNKNOWNS
 ↓
PLAN
 ↓
RESOURCE ALLOCATION
 ↓
EXECUTE
 ↓
OBSERVE
 ↓
VERIFY
 ↓
RECOVER
 ↓
UPDATE
 ↓
REPLAN
 ↓
OUTCOME
```

---

## 📚 Complete Engineering Documentation

| Document | Description |
| :--- | :--- |
| **[Progress Ledger](docs/PROGRESS.md)** | Real-time implementation progress, test pass rates, and milestone tracking. |
| **[Vision & Paradigm](docs/vision.md)** | Mission operating system vision, core loop, and design principles. |
| **[Product Requirements (PRD)](docs/product-requirements.md)** | Target users, user stories, MVP scope, non-goals, and KPIs. |
| **[Functional Requirements](docs/functional-requirements.md)** | Complete functional modules, state machines, and interface contracts. |
| **[Non-Functional Requirements](docs/non-functional-requirements.md)** | Performance, scalability, availability, security, and quality standards. |
| **[System Architecture](docs/system-architecture.md)** | Component topology, Cloud Run services, Pub/Sub event mesh, and persistence. |
| **[Agent Architecture & ADK](docs/agent-architecture.md)** | Google ADK runtime, specialized subagents, memory tiers, and task contracts. |
| **[World Model & Epistemic Engine](docs/world-model.md)** | Semantic entity graph, knowns vs assumptions vs unknowns, and state mutations. |
| **[Resource Brain & Governance](docs/resource-brain.md)** | Dynamic token budgeting, dollar spend caps, model routing, and rate backpressure. |
| **[Workflow Engine & DAG](docs/workflow-engine.md)** | Dynamic DAG generation, topological sorting, parallel dispatch, and live mutation. |
| **[Evidence & Verification Protocol](docs/evidence-and-verification.md)** | 4-level proof hierarchy, cryptographic SHA-256 validation, and GCS artifact topology. |
| **[Automated Recovery & Self-Healing](docs/recovery.md)** | Error taxonomy, exponential backoff, dynamic subtree repair, and HITL escalation. |
| **[Security & Governance](docs/security.md)** | IAM least privilege, Secret Manager, prompt injection defense, and sandbox isolation. |
| **[Database & Storage Schema](docs/database.md)** | Firestore document hierarchy, composite indexes, and Cloud Storage taxonomy. |
| **[API Specification](docs/api.md)** | REST endpoints, Server-Sent Events (SSE) telemetry, and WebSocket consoles. |
| **[Frontend & Mission Control PWA](docs/frontend.md)** | Next.js App Router, React Flow DAG canvas, xterm.js terminal, and dark mode UI. |
| **[Cloud Infrastructure & Terraform](docs/cloud.md)** | GCP serverless architecture and declarative Terraform modules. |
| **[Testing & QA Strategy](docs/testing.md)** | Test pyramid, emulator-driven integration tests, mock fixtures, and CI/CD gates. |
| **[Evaluation Framework](docs/evaluation.md)** | Quantitative benchmark suite (20 scenarios), trajectory evaluation, and metrics. |
| **[Hackathon Strategy & Demo](docs/hackathon.md)** | 3-minute live demonstration script, wow moments, and judging alignment. |
| **[Product Roadmap](docs/roadmap.md)** | Engineering milestones across Phase 0 (MVP), Phase 1 (Beta), Phase 2 (GA), and Phase 3. |
| **[Architecture Review & Contradiction Audit](docs/architecture-review.md)** | Comprehensive audit of contradictions, gaps, risks, and recommended fixes. |

---

## 🏛️ Architecture Decision Records (ADRs)

- **[ADR 0001: Google ADK & Gemini Model Tiering](docs/adr/0001-google-adk-and-gemini-agent-runtime.md)**
- **[ADR 0002: Firestore Document Hierarchy & World Model Persistence](docs/adr/0002-firestore-event-sourcing-and-world-model.md)**
- **[ADR 0003: Cloud Run & Pub/Sub Event-Driven Task Dispatch](docs/adr/0003-cloud-run-and-pubsub-mission-dispatch.md)**
- **[ADR 0004: Next.js / TypeScript Progressive Web Application (PWA)](docs/adr/0004-nextjs-pwa-mission-control.md)**
- **[ADR 0005: Four-Level Evidence Verification Hierarchy](docs/adr/0005-evidence-verification-hierarchy.md)**
- **[ADR 0006: Dynamic Token Budgeting & Resource Brain Governance](docs/adr/0006-token-budget-and-resource-brain.md)**

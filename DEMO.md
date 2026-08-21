# Agent-X End-to-End Demonstration Guide

This guide walks through the live interactive demonstration of Agent-X for hackathon judges, engineers, and mission commanders.

---

## 🎯 Demo Mission Scenario: Automated Database Migration & Performance Audit

In this scenario, Agent-X takes an open-ended database modernization goal, discovers legacy schemas, formulates a dynamic task DAG, handles unexpected benchmark failures autonomously, validates cryptographic proof, and delivers verified migration artifacts.

---

## Step-by-Step Walkthrough

### 1. Launch Mission Control Cockpit
- Navigate to `http://localhost:3000` (or your deployed Cloud Run URL).
- Inspect the **Fleet Dashboard** displaying system health, active missions, and aggregate token spend.

### 2. Formulate New Mission
- Click **New Mission** (`/missions/new`).
- Enter the mission parameters:
  ```json
  {
    "title": "Migrate SQLite Database to Cloud SQL PostgreSQL",
    "goal_statement": "Audit SQLite database, synthesize PostgreSQL DDL with indexes, execute schema migration, run performance benchmarks, and produce verified migration deliverables.",
    "max_usd_budget": 5.00,
    "max_runtime_minutes": 30
  }
  ```
- Click **Launch Mission**.

### 3. Observe Dynamic Graph Execution
- Navigate to **Mission Graph** (`/missions/[id]/graph`).
- Watch the Directed Acyclic Graph (DAG) synthesize and schedule tasks in parallel:
  - `Task 1: Audit SQLite Schema` (Routed to Gemini 2.5 Flash)
  - `Task 2: Synthesize PostgreSQL DDL` (Routed to Gemini 2.5 Pro)
  - `Task 3: Execute Benchmark Suite` (Routed to Gemini 2.5 Flash)

### 4. Inspect Resource Monitor & Causal "WHY"
- Click **Resources** (`/missions/[id]/resources`).
- View the 6-dimensional resource monitor:
  - Token consumption meter
  - Dollar spend vs. budget cap
  - Dynamic model routing distribution
- Review the Causal Allocation Timeline explaining why resources were reserved or reallocated.

### 5. Failure Injection & Autonomous Self-Healing
- During benchmark execution, a synthetic tool failure is triggered (e.g. data format mismatch).
- Navigate to **Failure Center** (`/missions/[id]/failures`).
- Observe the Recovery Engine in action:
  - Error classified as `DATA` failure.
  - Recovery strategy selected: `ALTERNATIVE_TOOL` with automatic parameter adjustments.
  - Workflow mutated and task re-executed to completion without crashing or user intervention.

### 6. Evidence Verification & Artifact Download
- Navigate to **Evidence Explorer** (`/missions/[id]/evidence`).
  - View verified claims, confidence scores, and supporting sources.
- Navigate to **Artifact Center** (`/missions/[id]/artifacts`).
  - Inspect generated deliverables: `Database Migration Report`, `PostgreSQL Schema DDL`, and `Benchmark Dataset`.
  - Click **Download** to save cryptographically verified artifacts directly to your machine.

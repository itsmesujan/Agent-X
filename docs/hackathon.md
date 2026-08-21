# Agent-X Hackathon Strategy & Live Demonstration Guide

## 1. Hackathon Narrative & Value Proposition

**Elevator Pitch:**  
*"Most autonomous agents are brittle prompt loops that hallucinate progress, break on the first error, and blow through token budgets. Agent-X is an Autonomous Mission Operating System powered by Gemini 2.5 and Google ADK. It transforms open-ended user objectives into a dynamic, self-healing, resource-bounded mission DAG—with cryptographic proof for every single step and live real-time cockpit control."*

---

## 2. Live Demo Script (3-Minute Walkthrough)

```mermaid
journey
    title 3-Minute Hackathon Demo Journey
    section 0:00 - 0:45 (The Goal)
      Submit Open-Ended Goal in PWA: 5: Commander
      Gemini 2.5 Pro Generates Live World Model: 5: System
      Interactive DAG Graph Expands on Canvas: 5: Commander
    section 0:45 - 1:45 (Parallel Execution & Evidence)
      Subagents Spawn on Cloud Run: 5: System
      Live Telemetry Streams to Mission Console: 5: Commander
      Level 1-4 Evidence Verifier Generates Proof Badges: 5: System
    section 1:45 - 2:30 (Injected Failure & Live Self-Healing)
      Injected Bug / Broken Test in Sandbox: 3: System
      Error Classifier Triggers Strategy B & Subtree Injected: 5: System
      Tester Agent Re-runs and Verifies Fix (Green Badge): 5: Commander
    section 2:30 - 3:00 (Deliverable & Audit Ledger)
      Complete Deliverable Verified & Exported: 5: Commander
      Resource Brain Demonstrates Budget Adherence: 5: Commander
```

### Step-by-Step Demo Flow
1. **The Objective (0:00 - 0:45)**:
   - In Mission Control PWA, type: *"Audit this microservice repository, fix the broken authentication endpoint, add unit tests, and verify all tests pass."*
   - Watch the World Model entity graph render immediately and the Task DAG generate with clear parallel branches.
2. **Execution & Evidence (0:45 - 1:45)**:
   - Click on the active Coder Agent node. Watch live terminal streaming as code is written and patched.
   - Point out the **Resource Brain** tracking exact token count and sub-cent dollar expenditure in real time.
3. **The 'WOW' Moment: Autonomous Self-Healing (1:45 - 2:30)**:
   - Show an intentional test regression detected by the Tester Agent.
   - Show the dynamic DAG mutation in real time: a repair node is injected, the Coder Agent receives the exact test failure context, writes the fix, and the Tester Agent re-runs until a green Level 4 Verification Badge is issued.
4. **Conclusion & Audit (2:30 - 3:00)**:
   - Click **View Evidence**. Show the side-by-side unified diff and the cryptographic SHA-256 proof record stored in GCS.

---

## 3. Alignment with Hackathon Judging Criteria

| Judging Criterion | How Agent-X Excels | Concrete Proof Point |
| :--- | :--- | :--- |
| **Technical Innovation & Architecture** | Complete closed-loop mission OS with dynamic DAG synthesis, live mutation, and epistemic state modeling. | Built with Google ADK runtime, Gemini 2.5 Pro/Flash, and Cloud Run. |
| **Real-World Impact & Utility** | Solves agent reliability, context drift, runaway costs, and lack of accountability. | Deterministic evidence verification and hard budget caps. |
| **User Experience & Design** | Sleek, cyber-ops Mission Control PWA with reactive canvas, live terminal, and interactive entity viewer. | Next.js, React Flow, xterm.js, Tailwind CSS, dark mode design system. |
| **Completeness & Execution** | End-to-end working system with automated evaluation suite and full Terraform deployment. | Automated evaluation runner scoring 20 benchmark missions. |

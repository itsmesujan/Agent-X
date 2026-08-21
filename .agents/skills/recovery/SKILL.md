---
name: recovery
description: Diagnoses task failures, classifies errors, applies self-healing strategies, and orchestrates rollbacks and HITL.
---

# Recovery Skill

## 1. Purpose
Diagnose task failures and verification rejections using the Agent-X Error Taxonomy, select and execute targeted self-healing strategies (retry, code fix, dependency injection, replan), and manage rollback and Human-in-the-Loop (HITL) escalations.

## 2. When to Use
- Whenever a task returns a non-zero exit code, unhandled exception, or timeout.
- When Level 1-4 Verification fails.
- When an external cloud or API dependency returns rate limit (429) or server errors (500/502/503).
- When initiating a state rollback or pausing for human intervention.

## 3. Constraints
- Max 3 automated replan attempts per mission branch before escalating to HITL.
- Non-idempotent failed tasks must be rolled back to pre-task state checkpoints before retrying.
- The main Git branch must never be modified during unverified recovery attempts.

## 4. Inputs
- Task error stack traces, compiler output, test failure diffs, and verification rejections.
- Current task node and pre-execution state checkpoint.

## 5. Outputs
- Error classification (`TRANSIENT_NETWORK`, `SYNTAX_ERROR`, `DEPENDENCY_MISSING`, `PERMISSION_DENIED`, etc.).
- Selected recovery strategy action (`RETRY_WITH_BACKOFF`, `INJECT_FIX_PROMPT`, `INJECT_SUBTREE`, `ESCALATE_HITL`).
- `HITLEscalationEvent` payloads emitted to Firestore and Mission Control.

## 6. Implementation Rules
1. Classify error using deterministic pattern matching before invoking LLM diagnostics.
2. Apply exponential backoff with full jitter for transient network or rate-limiting errors.
3. For syntax/compilation errors, re-invoke Coder Agent with exact file lines and compiler error messages.
4. For missing dependencies, dynamically inject prerequisite installation tasks into the DAG.
5. If retries are exhausted, transition mission to `PAUSED (HITL_REQUIRED)` and alert operator via PWA push notifications.

## 7. Testing Requirements
- Test error classifier accuracy on sample Python, TypeScript, Docker, and GCP IAM error logs.
- Verify that state checkpoints correctly restore prior entity states during rollback tests.

## 8. Failure Conditions
- Infinite retry loops on deterministic permission or syntax errors.
- Failing to pause mission when safety or budget boundaries are violated.

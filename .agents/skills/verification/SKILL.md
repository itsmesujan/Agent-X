---
name: verification
description: Implements the 4-Level Evidence Verification Protocol, independent auditor checks, and proof signing.
---

# Verification Skill

## 1. Purpose
Execute the mandatory 4-Level Evidence Verification Protocol (Syntactic, Execution, Artifact, Semantic/Integration) to mathematically and objectively certify task completion without hallucination.

## 2. When to Use
- After a subagent completes tool execution and claims task success.
- Prior to marking any `TaskNode` status as `VERIFIED`.
- When an independent Auditor Agent performs impartial acceptance criteria evaluation.

## 3. Constraints
- The subagent that implemented the task (e.g. Coder Agent) is strictly forbidden from certifying its own Level 4 verification.
- A task MUST pass all required levels sequentially (Level 1 -> Level 2 -> Level 3 -> Level 4) without skipping.
- Verification failures must output concrete diagnostics to guide automated recovery.

## 4. Inputs
- `SubagentTaskContract` with acceptance criteria.
- Tool stdout/stderr, generated files, test reports (JUnit XML), and GCS evidence links.

## 5. Outputs
- Signed `VerificationProof` object committed to Firestore.
- Verification status: `VERIFIED_PASS` or `VERIFICATION_FAILED`.
- Structured itemized check results (`checks: List[VerificationCheckItem]`).

## 6. Implementation Rules
1. **Level 1 (Syntactic)**: Assert exit code == 0 and output conforms to Pydantic schema.
2. **Level 2 (Execution)**: Assert required regex patterns appear in stdout and HTTP endpoints return 200.
3. **Level 3 (Artifact)**: Assert target files exist in GCS with non-zero size and verified SHA-256 hash.
4. **Level 4 (Semantic)**: Run automated test runners (`pytest`, `npm test`) and execute independent Auditor evaluation prompt.

## 7. Testing Requirements
- Test verifier against intentionally broken code/outputs; assert that it generates a fail proof with 0 false positives.
- Test HMAC-SHA256 signature generation and validation on proof payloads.

## 8. Failure Conditions
- Marking a task verified when unit tests fail or compiler errors are present.
- Self-certification by the implementing agent.

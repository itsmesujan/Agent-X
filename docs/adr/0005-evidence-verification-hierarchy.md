# ADR 0005: Four-Level Evidence Verification Hierarchy

## Status
**Accepted**

## Context
A critical vulnerability of existing LLM agents is hallucinated task completion. Agents frequently output "I have successfully fixed the bug" or "The security policy is deployed" without performing verification or generating proof. 

We need a deterministic mechanism to prevent hallucinated transitions and guarantee that task success is strictly grounded in objective reality.

## Decision
We enforce a mandatory **Four-Level Evidence Verification Hierarchy** for all tasks before any task may be marked `VERIFIED`:
1. **Level 1 (Syntactic Verification)**: Exit code is 0; outputs match strict Pydantic schemas; no unhandled exceptions.
2. **Level 2 (Execution Verification)**: Validated command stdout/stderr, regex match, or live HTTP status 200.
3. **Level 3 (Artifact Verification)**: Physical file/patch exists in Google Cloud Storage with non-zero bytes and matching SHA-256 hash.
4. **Level 4 (Semantic & Integration Verification)**: Passing automated test suite (`pytest`, `jest`) and independent verification by a decoupled Auditor Agent.

## Rationale
- **Zero Tolerance for Hallucination**: No task completes on LLM assertion alone.
- **Fail-Fast Granularity**: Level 1 and 2 failures trigger immediate local retries within seconds, avoiding costly and redundant Level 4 LLM evaluations.
- **Decoupled Evaluation**: Prohibits the implementing subagent (e.g. Coder Agent) from verifying its own output, ensuring impartial validation.
- **Immutable Audit Trail**: SHA-256 hashes and GCS evidence URIs provide non-repudiation for enterprise compliance and post-mission reviews.

## Consequences
- **Positive**: Eliminates hallucinated success, guarantees verifiable deliverables, generates enterprise-grade audit records.
- **Negative**: Adds slight execution latency (1-3 seconds per task) for artifact hashing and independent auditor evaluation.

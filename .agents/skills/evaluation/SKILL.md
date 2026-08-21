---
name: evaluation
description: Executes automated benchmark mission suites, calculates MSR, fidelity metrics, and generates scorecards.
---

# Evaluation Framework Skill

## 1. Purpose
Execute quantitative evaluation benchmark suites (20 scenarios) to evaluate reasoning quality, Mission Success Rate (MSR), verification fidelity, trajectory efficiency, and self-healing resilience of Agent-X.

## 2. When to Use
- When benchmarking new model releases (e.g. Gemini 2.5 Pro vs Flash).
- When evaluating prompt changes, subagent personas, or tool configurations.
- During release candidate qualification gates before deploying to production.
- When generating evaluation reports for hackathon submissions.

## 3. Constraints
- Evaluation benchmarks must execute in isolated ephemeral sandboxes to prevent test cross-contamination.
- Ground truth assertions must be strictly evaluated using deterministic Level 4 verification rules.
- Must compute quantitative scores: MSR ($\ge 85\%$), Verification Fidelity ($0\%$ false positives), Trajectory Efficiency, and Self-Healing Autonomy ($\ge 70\%$).

## 4. Inputs
- Benchmark scenario configurations (`evaluation/benchmarks/*.json`).
- Synthetic target repositories, injected error conditions, and ground-truth acceptance tests.

## 5. Outputs
- Standardized `evaluation_scorecard.json` and markdown evaluation summary.
- Step-by-step trajectory trace ledgers stored in GCS.
- Comparative regression reports against baseline scores.

## 6. Implementation Rules
1. Run evaluation scenarios via `python -m agentx.evaluation.runner`.
2. Score missions across 5 core dimensions: MSR, Verification Fidelity, Efficiency, Resilience, and Security.
3. Automatically flag any regression ($> 2\%$ drop in MSR) as a CI failure.

## 7. Testing Requirements
- Test evaluation runner with mock mission trajectories.
- Validate scoring calculations against known synthetic ground truth matrices.

## 8. Failure Conditions
- Evaluation runs that silently pass when ground-truth tests fail.
- Non-deterministic benchmark scenarios that produce erratic scores between runs.

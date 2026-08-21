---
name: testing
description: Establishes testing standards, unit/integration test suites, emulator setups, and mock harnesses for Agent-X.
---

# Testing & Quality Assurance Skill

## 1. Purpose
Define, author, execute, and automate comprehensive test suites across Agent-X, including Python unit tests, GCP emulator integration tests, subagent contract tests, and React component tests.

## 2. When to Use
- When developing new features, endpoints, algorithms, or subagent tools (TDD).
- When writing tests for state machine transitions, DAG topological sorting, or token math.
- When setting up local Firestore and Pub/Sub emulators.
- During CI test verification gates.

## 3. Constraints
- Every new feature MUST have corresponding unit and integration tests.
- Maintain minimum 85% line test coverage on all core modules.
- Never weaken assertions or swallow exceptions simply to make tests pass.
- Unit tests must be fast ($< 10\text{ s}$ for full unit suite) and deterministic (no flaky live API calls).

## 4. Inputs
- Python and TypeScript source code, API contracts, and task schemas.
- Test fixtures, recorded LLM responses, and synthetic repository trees.

## 5. Outputs
- Pytest test modules (`tests/unit/`, `tests/integration/`).
- Vitest component tests (`frontend/__tests__/`).
- JUnit XML and coverage reports (`coverage.xml`, `htmlcov/`).

## 6. Implementation Rules
1. Use `pytest`, `pytest-asyncio`, and `pytest-cov` for backend testing.
2. Use `respx` to mock HTTP external calls and recorded JSON fixtures for LLM responses.
3. Test against real Google Cloud Emulators (`gcloud emulators firestore start`, `gcloud emulators pubsub start`) for integration verification.
4. Structure test cases: Arrange, Act, Assert.

## 7. Testing Requirements
- Execute `pytest tests/ --cov=agentx --cov-report=term-missing`.
- Verify 0 test failures and zero unhandled async warnings.

## 8. Failure Conditions
- Tests that depend on live internet connectivity or live paid LLM tokens during CI runs.
- Disabling tests rather than fixing the underlying regression.

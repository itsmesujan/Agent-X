---
name: python
description: Standards, conventions, typing rules, and async execution guidelines for Agent-X Python backend.
---

# Python Engineering Skill

## 1. Purpose
Enforce robust, idiomatic, and strictly typed Python 3.12+ engineering practices across the Agent-X backend, worker runtimes, evaluation suites, and automation scripts.

## 2. When to Use
- When authoring or modifying any Python service, worker, tool wrapper, or data model.
- When configuring dependencies via `pyproject.toml` or `uv`.
- When implementing asynchronous event loops, background tasks, or Pub/Sub handlers.

## 3. Constraints
- Target Python 3.12+.
- Strict typing mandatory: 100% type annotations checked via `mypy --strict`.
- Zero bare exceptions (`except Exception: pass` is strictly prohibited).
- Use Pydantic v2 (`BaseModel`, `Field`, `ConfigDict`) for all data transfer objects and domain models.
- Package management via `uv` or modern `pyproject.toml` with pinned dependency hashes.

## 4. Inputs
- Python source files, module definitions, and Pydantic models.
- Task contracts and API request/response schemas.

## 5. Outputs
- Modular, object-oriented, and functional Python code.
- Pydantic models with serialization and validation logic.
- AsyncIO coroutines with structured concurrency (`asyncio.TaskGroup`).
- Pytest test suites with pytest-asyncio and coverage reports.

## 6. Implementation Rules
1. Format with `ruff format` and lint with `ruff check --fix`.
2. Handle all I/O asynchronously (`async/await`) using `httpx`, `asyncpg`, or Google Cloud async client libraries.
3. Manage concurrency safely with bounded semaphores (`asyncio.Semaphore`) to avoid connection exhaustion.
4. Structure logging using structured JSON with context fields (`mission_id`, `task_id`, `subagent_role`).

## 7. Testing Requirements
- Unit tests using `pytest` and `pytest-asyncio`.
- Minimum 85% line coverage on all business logic.
- Mock external network calls using `respx` or `unittest.mock`.

## 8. Failure Conditions
- Untyped function signatures or variables failing `mypy` strict check.
- Blocking synchronous network calls inside async event loops (e.g. using `requests` instead of `httpx`).
- Hardcoded secrets or credentials in Python source files.

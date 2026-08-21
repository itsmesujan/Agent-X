---
name: fastapi
description: Builds and manages the Agent-X REST, Server-Sent Events (SSE), and WebSocket APIs with FastAPI and Pydantic v2.
---

# FastAPI Skill

## 1. Purpose
Design, implement, test, and optimize the **Agent-X API Service** using **FastAPI** (Python 3.12) and **Pydantic v2**, supporting high-performance REST endpoints, Server-Sent Events (SSE) telemetry, and WebSocket consoles.

## 2. When to Use
- When creating or modifying backend API routes in `/api/v1/`.
- When implementing SSE streaming endpoints for real-time logs and token counters.
- When configuring WebSocket endpoints for interactive terminal sessions.
- When implementing request validation, error handlers, and authentication middleware.

## 3. Constraints
- Must use asynchronous endpoint handlers (`async def`).
- All request and response bodies must be typed using Pydantic v2 schemas.
- CORS must be explicitly configured for the Next.js PWA origin with credentials allowed.
- OpenTelemetry instrumentation must trace every incoming HTTP request.

## 4. Inputs
- HTTP requests from Mission Control PWA or external webhooks.
- Pub/Sub task dispatch and telemetry events.

## 5. Outputs
- Standardized JSON responses conforming to OpenAPI 3.1 specs.
- SSE stream packets (`text/event-stream`) formatted with event types and JSON data.
- WebSocket binary/text frames for bidirectional terminal consoles.

## 6. Implementation Rules
1. Organize endpoints into clean APIRouters: `/missions`, `/tasks`, `/entities`, `/telemetry`, `/actions`.
2. Use dependency injection (`fastapi.Depends`) for authentication, Firestore clients, and Secret Manager access.
3. Stream telemetry using `asyncio.Queue` and `EventSourceResponse` (via `sse-starlette` or custom SSE generator).
4. Use standard HTTP status codes: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 404 Not Found, 422 Unprocessable Entity, 500 Internal Server Error.

## 7. Testing Requirements
- Test all endpoints with `httpx.AsyncClient` in `pytest-asyncio`.
- Verify SSE stream connection, event delivery, and client disconnect cleanup.

## 8. Failure Conditions
- Synchronous blocking calls inside async route handlers.
- Endpoints returning untyped dictionaries instead of Pydantic response models.

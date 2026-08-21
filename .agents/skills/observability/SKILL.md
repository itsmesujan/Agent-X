---
name: observability
description: Implements OpenTelemetry distributed tracing, Google Cloud Logging, structured metrics, and audit exports.
---

# Observability & Telemetry Skill

## 1. Purpose
Instrument Agent-X services, workers, subagents, and Pub/Sub queues with **OpenTelemetry**, Google Cloud Trace, structured JSON logging, and real-time metric counters to ensure 100% operational transparency.

## 2. When to Use
- When adding distributed tracing spans across FastAPI requests, Pub/Sub events, and Google ADK turns.
- When configuring structured logging formats compatible with Google Cloud Logging.
- When recording Prometheus/Cloud Monitoring metrics (tokens consumed, active missions, task duration).
- When generating compliance audit exports.

## 3. Constraints
- All log messages must be structured JSON containing `trace_id`, `span_id`, `mission_id`, and `task_id`.
- Automated secret redaction MUST run on all log payloads prior to output.
- Avoid excessive log spam that could saturate Firestore write limits; send high-frequency debug logs to GCS/Cloud Logging and summarize for Firestore.

## 4. Inputs
- Trace contexts, error exceptions, latency measurements, and token consumption counters.

## 5. Outputs
- OpenTelemetry spans exported to Google Cloud Trace.
- Structured logs ingested by Google Cloud Logging.
- Real-time telemetry events streamed to Mission Control SSE.

## 6. Implementation Rules
1. Initialize OpenTelemetry SDK in FastAPI `lifespan` handler and worker entrypoints.
2. Inject traceparent headers into Pub/Sub message attributes to maintain trace continuity across async tasks.
3. Record standard metric counters: `agentx_mission_total`, `agentx_task_duration_seconds`, `agentx_tokens_used_total`, `agentx_active_workers`.

## 7. Testing Requirements
- Test trace propagation between API HTTP request and worker Pub/Sub consumer.
- Verify structured log parsing and secret redaction filters.

## 8. Failure Conditions
- Uncorrelated log statements missing `mission_id` or `trace_id`.
- Logging raw user passwords or API keys to standard output.

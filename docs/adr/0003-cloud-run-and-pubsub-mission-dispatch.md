# ADR 0003: Cloud Run & Pub/Sub Event-Driven Task Dispatch Architecture

## Status
**Accepted**

## Context
Agent-X requires a compute and messaging architecture capable of executing multi-agent tasks in parallel, handling bursty workloads, isolating containerized tool execution, and recovering gracefully from worker crashes or timeouts.

We evaluated Kubernetes (GKE), Google Cloud Functions, and Google Cloud Run paired with Google Cloud Pub/Sub.

## Decision
We adopt **Google Cloud Run (v2 Services)** paired with **Google Cloud Pub/Sub**:
- **API Service**: Cloud Run service exposing REST, SSE, and WebSocket interfaces.
- **Worker Pool**: Auto-scaling Cloud Run service receiving `TaskDispatchEvent` payloads via Pub/Sub push/pull subscriptions.
- **Pub/Sub Mesh**: Topics for task dispatch, real-time telemetry streaming, failure recovery events, and dead-letter queues.

## Rationale
- **Container Flexibility & Sandboxing**: Cloud Run allows custom Docker images containing full development toolchains (Python, Node.js, Git, Terraform, gcloud CLI) with exact environment reproducibility.
- **True Serverless Scale-to-Zero**: Eliminates baseline cluster costs when no missions are executing, while scaling horizontally to 100+ concurrent worker instances in seconds during heavy parallel DAG execution.
- **Reliable Message Delivery & Dead-Letter Support**: Pub/Sub guarantees at-least-once delivery, configurable retry backoff, and DLQ routing for poison messages.
- **Request & Execution Timeouts**: Cloud Run supports execution timeouts up to 60 minutes, accommodating long-running code generation and test execution tasks.

## Consequences
- **Positive**: Elastic auto-scaling, isolated container execution, simplified deployment via Terraform, built-in IAM security integration.
- **Negative**: Cold starts on worker scale-up (mitigated by setting minimum instances to 1 in production or using warm instance pools).

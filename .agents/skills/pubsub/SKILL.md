---
name: pubsub
description: Configures and manages Google Cloud Pub/Sub topics, push/pull subscriptions, message schemas, and DLQs.
---

# Google Cloud Pub/Sub Skill

## 1. Purpose
Architect, publish to, and consume from Google Cloud Pub/Sub topics and subscriptions for Agent-X asynchronous task dispatch, telemetry event streaming, failure recovery, and dead-letter queueing.

## 2. When to Use
- When dispatching unblocked `TaskNode` execution messages from the Coordinator to the Worker pool.
- When streaming high-throughput telemetry events and subagent thoughts.
- When configuring Pub/Sub push endpoints with OIDC authentication to Cloud Run.
- When configuring Dead Letter Queues (DLQ) and exponential backoff retry policies.

## 3. Constraints
- All published message payloads must be JSON-serialized strings conforming to typed Pydantic event schemas.
- Message ordering key must be set to `mission_id` when FIFO ordering is required for a mission branch.
- Push subscriptions must use authenticated Google Cloud Service Account OIDC tokens.

## 4. Inputs
- `TaskDispatchEvent`, `TelemetryEvent`, and `RecoveryEvent` objects.
- Pub/Sub subscription push endpoints.

## 5. Outputs
- Published message IDs and delivery status.
- Consumed and acknowledged task messages.
- DLQ forwarding for poison or repeatedly failed messages (max 5 delivery attempts).

## 6. Implementation Rules
1. Define topics: `agentx-task-dispatch`, `agentx-telemetry-events`, `agentx-recovery-events`, `agentx-dead-letter-queue`.
2. Configure Ack Deadline to 300s with minimum backoff 10s and maximum backoff 300s.
3. Workers must acknowledge (`ack`) messages only after task state is committed or lease extended during execution.
4. If an unexpected runtime exception occurs, either negative-acknowledge (`nack`) or allow deadline expiry for automatic redelivery.

## 7. Testing Requirements
- Test message publishing and ingestion against the local **Google Cloud Pub/Sub Emulator**.
- Test DLQ routing by triggering simulated repeated worker crashes.

## 8. Failure Conditions
- Dropping messages due to missing unhandled exception handlers in worker subscribers.
- Ingestion deadlock caused by unacknowledged poison messages without a configured DLQ.

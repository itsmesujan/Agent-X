---
name: cloud-run
description: Configures, packages, containerizes, and scales Google Cloud Run v2 services for API and worker pools.
---

# Google Cloud Run Skill

## 1. Purpose
Build, containerize, deploy, configure, and auto-scale serverless container instances on **Google Cloud Run (v2)** for the Agent-X API Service and distributed Worker Pools.

## 2. When to Use
- When writing or updating Dockerfiles for `agent-x-api` and `agent-x-worker`.
- When configuring Cloud Run CPU/Memory allocations, concurrency limits, and request timeouts.
- When setting up ingress settings (Public HTTPS for API, Internal-Only for Worker).
- When configuring service account identity, environment variables, and Cloud Secret Manager volume mounts.

## 3. Constraints
- API Service: Concurrency = 80, Min Instances = 1 (prod), Ingress = ALL.
- Worker Pool: Concurrency = 1–4, Min Instances = 0 (scale-to-zero), Max Instances = 100, Timeout = 600s, Ingress = INTERNAL_ONLY.
- Containers must execute as non-root user `UID 1001`.

## 4. Inputs
- Application source code (Python FastAPI, Google ADK runtime, worker scripts).
- Container configuration options (CPU, memory limits, execution timeout).

## 5. Outputs
- Multi-stage production `Dockerfile` configurations.
- Deployed Cloud Run v2 service instances with assigned HTTPS endpoints.
- Cloud Run health check endpoints (`/healthz`).

## 6. Implementation Rules
1. Use multi-stage Docker builds based on `python:3.12-slim` to minimize image size and attack surface.
2. Install necessary system tools (git, curl, terraform) in worker images without unnecessary build artifacts.
3. Expose standard HTTP port `8080`.
4. Ensure graceful termination on `SIGTERM` signals (flush logs, commit task checkpoints).

## 7. Testing Requirements
- Test local container builds with `docker build` and run smoke tests with `docker run`.
- Verify `/healthz` liveness and readiness probe responses.

## 8. Failure Conditions
- Worker instance memory crashes (OOM) due to unconstrained subagent tool processes.
- Container startup latency exceeding Cloud Run health check timeout limits.

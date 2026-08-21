# Hackathon Submission: System Architecture

Agent-X operates as a distributed, event-driven, cloud-native architecture on Google Cloud Platform:

```mermaid
graph TD
    subgraph ClientTier ["Mission Commander Cockpit (Next.js PWA)"]
        PWA["Next.js 15 PWA Mission Control<br/>(Cyber-Mission Dark Theme)"]
        WSClient["WebSocket Terminal & SSE Event Stream"]
    end

    subgraph EdgeTier ["Ingress & Security Boundary"]
        CloudArmor["Google Cloud Armor WAF"]
        LoadBalancer["Global Cloud HTTPS Load Balancer"]
    end

    subgraph ServiceTier ["Compute Layer (Google Cloud Run v2)"]
        API["agent-x-api (FastAPI REST / SSE / WS)"]
        WorkerPool["agent-x-worker (ADK Subagent Execution Sandbox)"]
    end

    subgraph IntelligenceTier ["Model & Agent Engine"]
        ADK["Google Agent Development Kit (ADK)"]
        GeminiPro["Gemini 2.5 Pro / 3.1 Pro (Architect & Verifier)"]
        GeminiFlash["Gemini 2.5 Flash / 3.7 Flash (Fast Workers)"]
    end

    subgraph EventTier ["Messaging Mesh (Google Cloud Pub/Sub)"]
        PSMission["agentx-mission-events"]
        PSTask["agentx-task-events"]
        PSRecovery["agentx-recovery-events"]
        PSDLQ["agentx-dead-letter-queue"]
    end

    subgraph StateTier ["Persistence & Evidence Storage"]
        Firestore["Google Cloud Firestore (Native Mode)"]
        GCS["Cloud Storage (Immutable Evidence Buckets)"]
        SecretMgr["Google Secret Manager (Dynamic Vault)"]
    end

    PWA --> LoadBalancer
    LoadBalancer --> API
    API <--> Firestore
    API --> PSMission
    API --> PSTask
    PSTask --> WorkerPool
    WorkerPool --> ADK
    ADK --> GeminiPro
    ADK --> GeminiFlash
    WorkerPool --> PSRecovery
    WorkerPool --> GCS
    WorkerPool <--> Firestore
    WorkerPool <--> SecretMgr
```

---

## Key Architectural Principles

1. **Kernel State Isolation**: Mission state, Task state, and Epistemic graph are cleanly separated and updated via atomic Firestore transactions and in-memory thread-safe locks.
2. **Asynchronous Task Dispatch**: Long-running subagent tasks execute decoupled from HTTP requests over Pub/Sub topics with exponential backoff and dead-letter queue containment.
3. **Defense-in-Depth Sandboxing**: All tool invocations occur with dropped capabilities, SSRF filters, path traversal sanitization, and AST-parsed code evaluation.

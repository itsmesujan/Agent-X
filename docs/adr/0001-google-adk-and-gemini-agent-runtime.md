# ADR 0001: Google ADK & Gemini Model Tiering for Agent Runtime

## Status
**Accepted**

## Context
Agent-X requires a robust agent execution framework to orchestrate specialized subagents (Architect, Coder, Tester, DevOps, Auditor) with structured tool calling, dynamic system prompting, and context management. We evaluated multiple approaches:
1. Building an ad-hoc custom prompting loop from scratch.
2. LangChain / CrewAI / AutoGen.
3. Google Agent Development Kit (ADK) + Google Gen AI SDK (`google-genai`) paired with Gemini 2.5 Pro and Gemini 2.5 Flash.

## Decision
We adopt the **Google Agent Development Kit (ADK)** combined with the official **Google Gen AI SDK** and a dual-tier Gemini model routing strategy:
- **Gemini 2.5 Pro**: Used for high-complexity cognitive reasoning tasks including Goal Deconstruction, Dynamic DAG Planning, Code Generation, Root-Cause Analysis, and Semantic Verification.
- **Gemini 2.5 Flash**: Used for high-throughput, low-latency tasks including Log Filtering, Sensory Extraction, Syntactic Verification, and Heartbeat Watchdogs.

## Rationale
- **Native Structured Output & Tool Calling**: Google ADK and Gemini offer first-class Pydantic schema validation for function calling with deterministic serialization.
- **Massive Context & Multimodal Native**: Gemini's long context window (1M+ tokens) allows processing large repositories and complex build logs without premature chunking.
- **Cost & Latency Optimization**: Dynamic routing between Flash and Pro keeps mission cost strictly within budget while preserving deep reasoning for critical decision paths.
- **Enterprise Ecosystem Alignment**: Direct integration with Google Cloud IAM, Secret Manager, and Cloud Run without third-party abstraction overhead.

## Consequences
- **Positive**: High reliability in tool calling, reduced latency, native schema enforcement, direct GCP integration.
- **Negative**: Tight coupling to the Google Gen AI ecosystem; multi-model abstractions must be implemented via the ADK provider interface if other LLMs are evaluated in future phases.

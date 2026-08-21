---
name: google-adk
description: Integrates and configures the Google Agent Development Kit (ADK) and Google Gen AI SDK for subagents.
---

# Google ADK Skill

## 1. Purpose
Provide precise implementation guidance for architecting, configuring, running, and debugging subagents built on the **Google Agent Development Kit (ADK)** and the **Google Gen AI SDK** (`google-genai`).

## 2. When to Use
- When defining subagent personas (Architect, Coder, Tester, DevOps, Auditor).
- When binding tools, function declarations, and Pydantic schemas to Google ADK agents.
- When managing multi-turn agent sessions, memory buffers, and context compression.
- When handling agent tool-calling loops, error recovery, and structured output parsing.

## 3. Constraints
- Must use official `google-genai` SDK patterns with typed parameters.
- Tool function signatures must include detailed docstrings and Pydantic type annotations.
- Subagent sessions must isolate memory to prevent cross-mission state contamination.

## 4. Inputs
- `SubagentTaskContract` containing task objectives, inputs, allowed paths, and tool bindings.
- System prompt templates tailored to specialized agent roles.

## 5. Outputs
- Configured ADK Agent instances ready for execution.
- Typed `SubagentTaskOutcome` payloads with generated artifacts and evidence URIs.
- Tool invocation telemetry logs and token usage metrics.

## 6. Implementation Rules
1. Define tools as clean Python functions returning structured Pydantic dictionaries.
2. Bind system instructions clearly demarcating role boundaries, security constraints, and output requirements.
3. Implement context compression when conversation history exceeds token thresholds ($> 1,500$ tokens per tool response).
4. Extract tool execution outputs deterministically and trap all tool-level exceptions into structured error envelopes.

## 7. Testing Requirements
- Test tool binding using mock LLM responses with `vcrpy` or synthetic function call fixtures.
- Verify that tool execution handles unexpected inputs gracefully without crashing the agent process.

## 8. Failure Conditions
- Passing untyped or unvalidated arguments to tool implementations.
- Infinite tool-calling loops (must enforce maximum iterations per task, default: 10 turns).
- Subagents bypassing tool security whitelists.

---
name: gemini
description: Best practices for prompting, model routing, multimodal processing, and token optimization with Gemini 2.5 Pro and Flash.
---

# Gemini Model Integration Skill

## 1. Purpose
Optimize prompting strategies, model selection, multimodal context ingestion, structured output schema generation, and token efficiency using the Gemini 2.5 family of models.

## 2. When to Use
- When authoring system instructions and few-shot prompts for specialized subagents.
- When configuring structured JSON output schemas (`response_schema` / `response_mime_type="application/json"`).
- When processing multimodal inputs (code diffs, UI screenshots, architecture diagrams, error traces).
- When tuning temperature, top-p, safety settings, and token limits.

## 3. Constraints
- Use **Gemini 2.5 Pro** for deep cognitive reasoning (DAG planning, code generation, root-cause diagnosis, semantic verification).
- Use **Gemini 2.5 Flash** for high-throughput, low-cost tasks (log filtering, regex extraction, syntactic verification, heartbeat watchdog).
- Never hardcode API keys; load dynamically from Google Secret Manager.

## 4. Inputs
- Prompt templates, context variables, user objectives, and tool output strings.
- Target Pydantic output schemas.

## 5. Outputs
- Deterministically parsed JSON objects conforming to target Pydantic schemas.
- Reasoning traces, code patches, architectural specifications, and verification judgments.
- Token consumption metrics (input, output, cached tokens).

## 6. Implementation Rules
1. Always enable structured output mode for machine-parsed responses.
2. Leverage Context Caching for large static context blocks (e.g. repository file trees or base architecture docs) to reduce cost by up to 75%.
3. Set temperature to `0.1` for deterministic code generation and verification; set to `0.3` for creative architectural planning.
4. Wrap all untrusted third-party inputs in `<untrusted_content>` tags to prevent prompt injection.

## 7. Testing Requirements
- Test prompt stability across multiple iterations using deterministic seeds where supported.
- Verify schema validation error handling when the model produces malformed JSON.

## 8. Failure Conditions
- Using Gemini 2.5 Pro for trivial formatting tasks, causing budget exhaustion.
- Missing error handling for HTTP 429 (ResourceExhausted) or content filtering blocks.

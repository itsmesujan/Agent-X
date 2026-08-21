---
name: hackathon-submission
description: Prepares pitch narrative, 3-minute video scripts, demonstration sandboxes, and judge evaluation materials.
---

# Hackathon Submission Skill

## 1. Purpose
Prepare, polish, structure, and validate the **Agent-X Hackathon Submission Package**, ensuring perfect alignment with judging criteria, a compelling 3-minute video demonstration, high-impact architecture diagrams, and a working live demo.

## 2. When to Use
- When preparing the final hackathon submission repository, README, and video script.
- When configuring the live demonstration sandbox and synthetic showcase scenarios.
- When validating that all judging criteria (Technical Innovation, Real-World Impact, UX, Completeness) have strong concrete proof points.

## 3. Constraints
- The demonstration MUST show real, working execution (no fake mock screens or static video tricks).
- The video pitch must strictly respect time limits (under 3 minutes).
- Highlight Google ADK, Gemini 2.5 Pro/Flash, and Google Cloud Run prominently.

## 4. Inputs
- Final architecture documents, benchmark scorecards, and live demo recordings.
- `/docs/hackathon.md` and `/docs/vision.md`.

## 5. Outputs
- Complete submission README with live demo link and video embed.
- 3-Minute demonstration script and timing cue sheet.
- Judge evaluation evidence matrix mapping every criterion to codebase files.
- Exported architectural graphics and UI demonstration captures.

## 6. Implementation Rules
1. Structure pitch: The Problem (brittle agents, hallucinated progress) -> The Solution (Agent-X closed-loop mission OS) -> The Tech (Gemini 2.5 + Google ADK + Cloud Run) -> The Live Demo (Dynamic DAG + Self-Healing + Evidence Proof) -> The Impact.
2. Ensure the demo clearly highlights the "WOW" moment: Intentional test failure -> automated root-cause diagnosis -> live DAG replanning -> verified green pass with SHA-256 proof.
3. Verify that public demo instances have pre-configured safety quotas and clean seed data.

## 7. Testing Requirements
- Dry-run the 3-minute pitch against a timer to guarantee it completes within 180 seconds.
- Test the live demo flow 5 consecutive times on clean staging environments to ensure 100% reliability.

## 8. Failure Conditions
- Live demo encountering unhandled crashes during video recording or judge review.
- Missing clear explanations of Google Cloud / Gemini technical integration.

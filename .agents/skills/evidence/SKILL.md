---
name: evidence
description: Captures, hashes, archives, and organizes immutable execution evidence artifacts in Google Cloud Storage.
---

# Evidence Skill

## 1. Purpose
Capture raw execution outputs, standard streams, network logs, screenshots, unified diffs, and build artifacts, archiving them in Google Cloud Storage with cryptographic SHA-256 integrity hashes.

## 2. When to Use
- Whenever a subagent executes a tool or produces a deliverable.
- When generating audit proofs for Level 3 Artifact Verification.
- When archiving full execution transcripts for post-mission compliance review.

## 3. Constraints
- All evidence artifacts must be stored immutably in GCS under the standard mission naming hierarchy (`gs://agentx-evidence-artifacts-{env}/missions/{missionId}/tasks/{taskId}/`).
- Files must be hashed with SHA-256 before committing the evidence record to Firestore.
- Sensitive credentials must be redacted from evidence artifacts before GCS upload.

## 4. Inputs
- Raw tool stdout/stderr strings, generated source files, diff patches, and screenshots.
- Mission ID and Task ID metadata.

## 5. Outputs
- GCS Object URIs (`gs://...`).
- Signed `ArtifactMetadata` with filename, MIME type, byte size, and SHA-256 hex digest.
- Redacted execution transcripts in JSONL format.

## 6. Implementation Rules
1. Compute SHA-256 checksums locally prior to initiating GCS multipart uploads.
2. Structure GCS storage paths cleanly: `missions/{missionId}/tasks/{taskId}/artifacts/{filename}`.
3. Attach GCS URIs to task outputs in Firestore to allow one-click download in Mission Control.

## 7. Testing Requirements
- Test SHA-256 calculation and verify tamper detection by altering 1 byte in a test fixture.
- Verify GCS upload error handling and retry logic.

## 8. Failure Conditions
- Committing empty or 0-byte files as valid evidence.
- Uploading unredacted API keys or secrets to Cloud Storage.

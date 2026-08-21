---
name: security
description: Audits and enforces IAM least privilege, Secret Manager dynamic retrieval, prompt injection defense, and sandboxing.
---

# Security Skill

## 1. Purpose
Enforce Zero Trust security across Agent-X, manage Google Cloud IAM permissions, secure dynamic secret retrieval, implement automated credential redaction, defend against prompt injection, and audit container sandboxing.

## 2. When to Use
- When configuring service accounts, IAM roles, and Workload Identity Federation.
- When retrieving credentials from Google Secret Manager.
- When implementing or testing token redaction on logs and telemetry streams.
- When evaluating tool commands against security whitelists and blacklists.
- During security audits and vulnerability assessments.

## 3. Constraints
- Zero hardcoded secrets anywhere in source code, Dockerfiles, or tests.
- Tool processes must run as non-root user `UID 1001` with `CAP_DROP_ALL`.
- Destructive commands (`rm -rf /`, `gcloud projects delete`) are strictly blacklisted.
- All untrusted external inputs must be wrapped in `<untrusted_content>` tags.

## 4. Inputs
- Code repositories, Dockerfile configurations, Terraform IAM modules, and execution logs.
- Secret Manager key identifiers.

## 5. Outputs
- Dynamic in-memory secret references with 5-minute TTL cache.
- Redacted log streams free of API keys, bearer tokens, and passwords.
- Security audit reports and policy violation notices.

## 6. Implementation Rules
1. Never log secrets or include raw credential values in LLM prompt contexts.
2. Run automated regex filters on all stdout/stderr streams before writing to Firestore or SSE.
3. Deny direct access to the GCP instance metadata server from worker tool containers.
4. Restrict all Google Cloud Service Accounts to granular, least-privilege roles.

## 7. Testing Requirements
- Test secret redaction against a fixture suite of fake Google, GitHub, AWS, and JWT tokens.
- Validate that attempts to execute blacklisted bash commands return immediate security denials.

## 8. Failure Conditions
- Committing secrets to Git or persisting plain-text tokens to Firestore/GCS.
- Running tool containers with root privileges or full host network access.

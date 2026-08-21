---
name: terraform
description: Provisions and manages 100% of Agent-X GCP cloud infrastructure declaratively using modular Terraform.
---

# Terraform Infrastructure as Code Skill

## 1. Purpose
Define, provision, modify, and audit all Google Cloud Platform infrastructure for Agent-X using modular, declarative **Terraform (HCL)** configurations.

## 2. When to Use
- When defining or updating GCP resources: Cloud Run, Pub/Sub, Firestore, Cloud Storage, Secret Manager, Cloud Armor, IAM.
- When configuring environment variables, service accounts, and IAM role bindings.
- When applying infrastructure changes to `dev` or `prod` environments.

## 3. Constraints
- 100% of cloud resources must be managed via Terraform (no manual console provisioning).
- Use modular structure under `/terraform/modules/` and environment folders `/terraform/environments/`.
- All state files must be stored securely in a remote GCS backend with state locking enabled.
- Never hardcode project IDs or secrets in `.tf` files; use variables and `.tfvars`.

## 4. Inputs
- Infrastructure requirements, region targets, environment names (`dev`, `prod`).
- Terraform variable definitions (`variables.tf`).

## 5. Outputs
- Modular HCL files (`main.tf`, `variables.tf`, `outputs.tf`).
- Validated execution plans (`terraform plan`).
- Provisioned cloud resources with exported endpoints and resource IDs.

## 6. Implementation Rules
1. Organize into modules: `cloud_run`, `pubsub`, `firestore`, `storage`, `secret_manager`, `iam`, `cloud_armor`.
2. Format all code with `terraform fmt -check` and validate with `terraform validate`.
3. Apply least-privilege IAM roles to service accounts (`sa-agentx-api`, `sa-agentx-worker`).
4. Enable object versioning and lifecycle rules (90-day retention) on evidence storage buckets.

## 7. Testing Requirements
- Run `terraform validate` and `tflint` on all modules in CI.
- Execute `terraform plan` and assert that no unintended resource destructions are scheduled.

## 8. Failure Conditions
- Hardcoded secrets or credentials committed in `.tf` files.
- Modifying cloud resources manually out-of-band causing Terraform state drift.

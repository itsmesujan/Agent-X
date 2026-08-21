# Service Accounts
resource "google_service_account" "sa_agentx_api" {
  project      = var.project_id
  account_id   = "sa-agentx-api-${var.environment}"
  display_name = "Agent-X API Coordinator Service Account (${var.environment})"
  description  = "Service account for Agent-X FastAPI Coordinator and Mission Orchestrator"
}

resource "google_service_account" "sa_agentx_worker" {
  project      = var.project_id
  account_id   = "sa-agentx-worker-${var.environment}"
  display_name = "Agent-X Worker Execution Service Account (${var.environment})"
  description  = "Service account for Agent-X autonomous subagent workers and tool execution sandbox"
}

resource "google_service_account" "sa_agentx_ci" {
  project      = var.project_id
  account_id   = "sa-agentx-ci-${var.environment}"
  display_name = "Agent-X Evaluation & CI Service Account (${var.environment})"
  description  = "Service account for benchmark evaluation runner and CI smoke testing"
}

# Least-Privilege IAM Roles: API Coordinator
locals {
  api_roles = [
    "roles/firestore.dataEditor",
    "roles/pubsub.publisher",
    "roles/storage.objectViewer",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent"
  ]

  worker_roles = [
    "roles/firestore.dataEditor",
    "roles/pubsub.subscriber",
    "roles/pubsub.publisher",
    "roles/storage.objectAdmin",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent"
  ]

  ci_roles = [
    "roles/storage.objectViewer",
    "roles/run.invoker"
  ]
}

resource "google_project_iam_member" "api_role_bindings" {
  for_each = toset(local.api_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.sa_agentx_api.email}"
}

resource "google_project_iam_member" "worker_role_bindings" {
  for_each = toset(local.worker_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.sa_agentx_worker.email}"
}

resource "google_project_iam_member" "ci_role_bindings" {
  for_each = toset(local.ci_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.sa_agentx_ci.email}"
}

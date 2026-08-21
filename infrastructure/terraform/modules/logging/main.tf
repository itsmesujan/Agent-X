# 1. Log-Based Metric: Task Failures
resource "google_logging_metric" "task_failures" {
  project = var.project_id
  name    = "agentx_task_failures_${var.environment}"
  filter  = "resource.type=\"cloud_run_revision\" AND jsonPayload.event_type=\"TASK_FAILED\""

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    display_name = "Agent-X Task Failures (${var.environment})"
  }
}

# 2. Log-Based Metric: Security Policy Rejections
resource "google_logging_metric" "security_rejections" {
  project = var.project_id
  name    = "agentx_security_rejections_${var.environment}"
  filter  = "resource.type=\"cloud_run_revision\" AND (textPayload=~\"SECURITY_DENIED\" OR jsonPayload.message=~\"SECURITY_DENIED\" OR jsonPayload.error=~\"SSRF\")"

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    display_name = "Agent-X Security Policy Rejections (${var.environment})"
  }
}

# 3. Log-Based Metric: Self-Healing Recoveries
resource "google_logging_metric" "recovery_actions" {
  project = var.project_id
  name    = "agentx_recovery_actions_${var.environment}"
  filter  = "resource.type=\"cloud_run_revision\" AND (jsonPayload.event_type=\"RECOVERY_APPLIED\" OR jsonPayload.event_type=\"SELF_HEALED\")"

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    display_name = "Agent-X Automated Self-Healing Actions (${var.environment})"
  }
}

# 4. Long-Term Audit Log Sink to Cloud Storage
resource "google_logging_project_sink" "audit_sink" {
  project                = var.project_id
  name                   = "agentx-security-audit-sink-${var.environment}"
  destination            = "storage.googleapis.com/${var.audit_destination_bucket}"
  filter                 = "severity >= WARNING OR jsonPayload.security_event = true"
  unique_writer_identity = true
}

# Grant the Sink's Writer Identity permissions on the destination bucket
resource "google_storage_bucket_iam_member" "sink_writer" {
  bucket = var.audit_destination_bucket
  role   = "roles/storage.objectCreator"
  member = google_logging_project_sink.audit_sink.writer_identity
}

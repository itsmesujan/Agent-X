output "task_failures_metric_name" {
  description = "Name of the task failures log metric"
  value       = google_logging_metric.task_failures.name
}

output "security_rejections_metric_name" {
  description = "Name of the security rejections log metric"
  value       = google_logging_metric.security_rejections.name
}

output "recovery_actions_metric_name" {
  description = "Name of the recovery actions log metric"
  value       = google_logging_metric.recovery_actions.name
}

output "audit_sink_id" {
  description = "ID of the audit logging sink"
  value       = google_logging_project_sink.audit_sink.id
}

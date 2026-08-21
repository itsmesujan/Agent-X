output "alert_policy_error_rate_id" {
  description = "ID of the high error rate alert policy"
  value       = google_monitoring_alert_policy.high_error_rate.id
}

output "alert_policy_dlq_id" {
  description = "ID of the DLQ backlog alert policy"
  value       = google_monitoring_alert_policy.dlq_backlog.id
}

output "dashboard_id" {
  description = "ID of the Agent-X operational dashboard"
  value       = google_monitoring_dashboard.agentx_dashboard.id
}

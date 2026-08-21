output "api_service_url" {
  description = "Cloud Run URI for the Agent-X API Coordinator"
  value       = module.cloud_run.api_service_url
}

output "evidence_bucket_name" {
  description = "GCS bucket for evidence artifacts and verification proofs"
  value       = module.storage.evidence_bucket_name
}

output "database_name" {
  description = "Firestore Native Database name"
  value       = module.firestore.database_name
}

output "task_events_topic_id" {
  description = "Pub/Sub topic ID for task dispatch"
  value       = module.pubsub.task_events_topic_id
}

output "sa_api_email" {
  description = "Service account email for API Coordinator"
  value       = module.iam.sa_api_email
}

output "sa_worker_email" {
  description = "Service account email for Subagent Workers"
  value       = module.iam.sa_worker_email
}

output "dashboard_id" {
  description = "Cloud Monitoring Dashboard ID"
  value       = module.monitoring.dashboard_id
}

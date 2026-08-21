output "api_service_url" {
  description = "Production API URL"
  value       = module.prod_infrastructure.api_service_url
}

output "evidence_bucket_name" {
  description = "Production Evidence Bucket"
  value       = module.prod_infrastructure.evidence_bucket_name
}

output "database_name" {
  description = "Production Firestore Native Database Name"
  value       = module.prod_infrastructure.database_name
}

output "task_events_topic_id" {
  description = "Production Pub/Sub Task Events Topic"
  value       = module.prod_infrastructure.task_events_topic_id
}

output "sa_api_email" {
  description = "Production API Coordinator Service Account Email"
  value       = module.prod_infrastructure.sa_api_email
}

output "sa_worker_email" {
  description = "Production Worker Service Account Email"
  value       = module.prod_infrastructure.sa_worker_email
}

output "dashboard_id" {
  description = "Production Monitoring Dashboard ID"
  value       = module.prod_infrastructure.dashboard_id
}

output "sa_api_email" {
  description = "Email of the API Coordinator service account"
  value       = google_service_account.sa_agentx_api.email
}

output "sa_api_id" {
  description = "Resource ID of the API Coordinator service account"
  value       = google_service_account.sa_agentx_api.id
}

output "sa_worker_email" {
  description = "Email of the Worker service account"
  value       = google_service_account.sa_agentx_worker.email
}

output "sa_worker_id" {
  description = "Resource ID of the Worker service account"
  value       = google_service_account.sa_agentx_worker.id
}

output "sa_ci_email" {
  description = "Email of the CI / Evaluation service account"
  value       = google_service_account.sa_agentx_ci.email
}

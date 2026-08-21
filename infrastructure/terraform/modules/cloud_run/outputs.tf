output "api_service_url" {
  description = "URI endpoint of the API Coordinator service"
  value       = google_cloud_run_v2_service.api.uri
}

output "api_service_name" {
  description = "Name of the API Coordinator service"
  value       = google_cloud_run_v2_service.api.name
}

output "worker_service_name" {
  description = "Name of the Worker service"
  value       = google_cloud_run_v2_service.worker.name
}

output "worker_service_uri" {
  description = "URI endpoint of the Worker service"
  value       = google_cloud_run_v2_service.worker.uri
}

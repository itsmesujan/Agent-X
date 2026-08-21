output "api_service_url" {
  description = "Dev API URL"
  value       = module.dev_infrastructure.api_service_url
}

output "evidence_bucket_name" {
  description = "Dev Evidence Bucket"
  value       = module.dev_infrastructure.evidence_bucket_name
}

output "dashboard_id" {
  description = "Dev Operations Dashboard"
  value       = module.dev_infrastructure.dashboard_id
}

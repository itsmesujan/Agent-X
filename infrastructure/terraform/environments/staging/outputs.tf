output "api_service_url" {
  description = "Staging API URL"
  value       = module.staging_infrastructure.api_service_url
}

output "evidence_bucket_name" {
  description = "Staging Evidence Bucket"
  value       = module.staging_infrastructure.evidence_bucket_name
}

output "dashboard_id" {
  description = "Staging Operations Dashboard"
  value       = module.staging_infrastructure.dashboard_id
}

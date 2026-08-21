output "evidence_bucket_name" {
  description = "Name of the evidence and artifacts storage bucket"
  value       = google_storage_bucket.evidence_artifacts.name
}

output "evidence_bucket_url" {
  description = "URI of the evidence and artifacts storage bucket"
  value       = google_storage_bucket.evidence_artifacts.url
}

output "backups_bucket_name" {
  description = "Name of the backups storage bucket"
  value       = google_storage_bucket.backups.name
}

output "backups_bucket_url" {
  description = "URI of the backups storage bucket"
  value       = google_storage_bucket.backups.url
}

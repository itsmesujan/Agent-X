variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
}

variable "audit_destination_bucket" {
  type        = string
  description = "Cloud Storage bucket name for long-term audit log retention"
}

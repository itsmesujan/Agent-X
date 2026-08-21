variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  description = "GCP Region for Firestore database"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
  default     = "dev"
}

variable "enable_pitr" {
  type        = bool
  description = "Enable Point In Time Recovery (recommended for prod)"
  default     = false
}

variable "delete_protection" {
  type        = bool
  description = "Prevent accidental database deletion"
  default     = false
}

variable "project_id" {
  type        = string
  description = "Google Cloud Project ID for Dev environment"
}

variable "region" {
  type        = string
  description = "GCP Region for Dev deployment"
  default     = "us-central1"
}

variable "notification_email" {
  type        = string
  description = "Alert notification email"
  default     = "dev-alerts@agentx.internal"
}

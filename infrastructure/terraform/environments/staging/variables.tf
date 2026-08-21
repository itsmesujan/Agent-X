variable "project_id" {
  type        = string
  description = "Google Cloud Project ID for Staging environment"
}

variable "region" {
  type        = string
  description = "GCP Region for Staging deployment"
  default     = "us-central1"
}

variable "notification_email" {
  type        = string
  description = "Alert notification email"
  default     = "staging-alerts@agentx.internal"
}

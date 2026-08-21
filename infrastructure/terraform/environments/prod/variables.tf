variable "project_id" {
  type        = string
  description = "Google Cloud Project ID for Production environment"
}

variable "region" {
  type        = string
  description = "GCP Region for Production deployment"
  default     = "us-central1"
}

variable "notification_email" {
  type        = string
  description = "Alert notification email for Production on-call team"
  default     = "ops-oncall@agentx.internal"
}

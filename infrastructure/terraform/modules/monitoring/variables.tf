variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
}

variable "notification_email" {
  type        = string
  description = "Alert notification email address"
  default     = "alerts@agentx.internal"
}

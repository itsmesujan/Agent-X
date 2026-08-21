variable "project_id" {
  type        = string
  description = "Google Cloud Project ID"
}

variable "region" {
  type        = string
  description = "Default Google Cloud Region"
  default     = "us-central1"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
  default     = "dev"
}

variable "notification_email" {
  type        = string
  description = "Email for operational alerts"
  default     = "alerts@agentx.internal"
}

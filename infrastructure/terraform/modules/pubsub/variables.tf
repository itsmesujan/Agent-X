variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
}

variable "message_retention_duration" {
  type        = string
  description = "Retention duration for Pub/Sub messages (e.g. 604800s for 7 days)"
  default     = "604800s"
}

variable "ack_deadline_seconds" {
  type        = number
  description = "Acknowledgment deadline for pull subscriptions in seconds"
  default     = 120
}

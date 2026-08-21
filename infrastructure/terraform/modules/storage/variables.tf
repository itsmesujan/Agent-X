variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
}

variable "region" {
  type        = string
  description = "GCP Region or Multi-Region for storage buckets"
  default     = "US"
}

variable "retention_days" {
  type        = number
  description = "Retention period in days for evidence objects before deletion or archiving"
  default     = 90
}

variable "nearline_transition_days" {
  type        = number
  description = "Days after which objects transition to NEARLINE cold tier"
  default     = 30
}

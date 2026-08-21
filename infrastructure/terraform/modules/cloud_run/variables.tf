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
  description = "GCP Region for Cloud Run deployment"
}

variable "sa_api_email" {
  type        = string
  description = "Email of the API Coordinator service account"
}

variable "sa_worker_email" {
  type        = string
  description = "Email of the Worker service account"
}

variable "pubsub_task_topic" {
  type        = string
  description = "Pub/Sub Topic ID for task dispatch"
}

variable "evidence_bucket_name" {
  type        = string
  description = "Name of the evidence Cloud Storage bucket"
}

variable "gemini_secret_id" {
  type        = string
  description = "Secret ID for Gemini API Key in Secret Manager"
}

variable "session_secret_id" {
  type        = string
  description = "Secret ID for Session Secret in Secret Manager"
}

variable "api_min_instances" {
  type        = number
  description = "Minimum instance count for API service"
  default     = 0
}

variable "api_max_instances" {
  type        = number
  description = "Maximum instance count for API service"
  default     = 10
}

variable "worker_min_instances" {
  type        = number
  description = "Minimum instance count for Worker service"
  default     = 0
}

variable "worker_max_instances" {
  type        = number
  description = "Maximum instance count for Worker service"
  default     = 10
}

variable "api_cpu" {
  type        = string
  description = "CPU limit for API service"
  default     = "2000m"
}

variable "api_memory" {
  type        = string
  description = "Memory limit for API service"
  default     = "2Gi"
}

variable "worker_cpu" {
  type        = string
  description = "CPU limit for Worker service"
  default     = "2000m"
}

variable "worker_memory" {
  type        = string
  description = "Memory limit for Worker service"
  default     = "4Gi"
}

variable "allow_unauthenticated" {
  type        = bool
  description = "Allow unauthenticated invocations to the API (e.g. for public web ingress)"
  default     = true
}

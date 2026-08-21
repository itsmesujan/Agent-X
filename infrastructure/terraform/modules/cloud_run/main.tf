# 1. Agent-X API Coordinator Service
resource "google_cloud_run_v2_service" "api" {
  project  = var.project_id
  name     = "agent-x-api-${var.environment}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = var.sa_api_email
    timeout         = "300s"

    scaling {
      min_instance_count = var.api_min_instances
      max_instance_count = var.api_max_instances
    }

    containers {
      image = "gcr.io/${var.project_id}/agent-x-api:${var.environment}"

      resources {
        limits = {
          cpu    = var.api_cpu
          memory = var.api_memory
        }
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "PUBSUB_TASK_TOPIC"
        value = var.pubsub_task_topic
      }

      env {
        name  = "EVIDENCE_BUCKET"
        value = var.evidence_bucket_name
      }

      env {
        name  = "OTEL_SERVICE_NAME"
        value = "agent-x-api-${var.environment}"
      }

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = var.gemini_secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "SESSION_SECRET"
        value_source {
          secret_key_ref {
            secret  = var.session_secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/healthz"
          port = 8000
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/healthz"
          port = 8000
        }
        period_seconds = 15
      }
    }
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    component   = "api"
  }
}

# 2. Agent-X Worker Execution Pool Service
resource "google_cloud_run_v2_service" "worker" {
  project  = var.project_id
  name     = "agent-x-worker-${var.environment}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    service_account = var.sa_worker_email
    timeout         = "900s" # 15 minutes for long-running subagent tasks

    scaling {
      min_instance_count = var.worker_min_instances
      max_instance_count = var.worker_max_instances
    }

    containers {
      image = "gcr.io/${var.project_id}/agent-x-worker:${var.environment}"

      resources {
        limits = {
          cpu    = var.worker_cpu
          memory = var.worker_memory
        }
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "EVIDENCE_BUCKET"
        value = var.evidence_bucket_name
      }

      env {
        name  = "OTEL_SERVICE_NAME"
        value = "agent-x-worker-${var.environment}"
      }

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = var.gemini_secret_id
            version = "latest"
          }
        }
      }
    }
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    component   = "worker"
  }
}

# Public / Ingress IAM Binding for API Service
resource "google_cloud_run_service_iam_member" "api_public_access" {
  count    = var.allow_unauthenticated ? 1 : 0
  project  = var.project_id
  location = var.region
  service  = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

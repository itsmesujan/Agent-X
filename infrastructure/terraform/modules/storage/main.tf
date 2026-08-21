# Evidence & Deliverable Artifacts Bucket
resource "google_storage_bucket" "evidence_artifacts" {
  project                     = var.project_id
  name                        = "agentx-evidence-${var.project_id}-${var.environment}"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy               = var.environment != "prod"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
    condition {
      age = var.nearline_transition_days
    }
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = var.retention_days
    }
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    system      = "agent-x"
  }
}

# Immutable Backups & Audit State Bucket
resource "google_storage_bucket" "backups" {
  project                     = var.project_id
  name                        = "agentx-backups-${var.project_id}-${var.environment}"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy               = var.environment != "prod"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
    condition {
      age = 90
    }
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    system      = "agent-x"
  }
}

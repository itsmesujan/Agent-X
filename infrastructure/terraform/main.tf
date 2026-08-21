terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. IAM Service Accounts & Role Bindings
module "iam" {
  source      = "./modules/iam"
  project_id  = var.project_id
  environment = var.environment
}

# 2. Cloud Firestore Native Database
module "firestore" {
  source            = "./modules/firestore"
  project_id        = var.project_id
  region            = var.region
  environment       = var.environment
  enable_pitr       = var.environment == "prod"
  delete_protection = var.environment == "prod"
}

# 3. Pub/Sub Messaging Topology
module "pubsub" {
  source      = "./modules/pubsub"
  project_id  = var.project_id
  environment = var.environment
}

# 4. Cloud Storage Buckets
module "storage" {
  source         = "./modules/storage"
  project_id     = var.project_id
  environment    = var.environment
  region         = var.region
  retention_days = var.environment == "prod" ? 365 : 90
}

# 5. Secret Manager Declarations
module "secret_manager" {
  source      = "./modules/secret_manager"
  project_id  = var.project_id
  environment = var.environment
}

# 6. Cloud Run API & Worker Pool
module "cloud_run" {
  source               = "./modules/cloud_run"
  project_id           = var.project_id
  environment          = var.environment
  region               = var.region
  sa_api_email         = module.iam.sa_api_email
  sa_worker_email      = module.iam.sa_worker_email
  pubsub_task_topic    = module.pubsub.task_events_topic_id
  evidence_bucket_name = module.storage.evidence_bucket_name
  gemini_secret_id     = module.secret_manager.gemini_secret_id
  session_secret_id    = module.secret_manager.session_secret_id
  api_min_instances    = var.environment == "prod" ? 2 : 0
  worker_min_instances = var.environment == "prod" ? 1 : 0
}

# 7. Cloud Logging & Audit Sinks
module "logging" {
  source                   = "./modules/logging"
  project_id               = var.project_id
  environment              = var.environment
  audit_destination_bucket = module.storage.backups_bucket_name
}

# 8. Cloud Monitoring & Alerts
module "monitoring" {
  source             = "./modules/monitoring"
  project_id         = var.project_id
  environment        = var.environment
  notification_email = var.notification_email
}

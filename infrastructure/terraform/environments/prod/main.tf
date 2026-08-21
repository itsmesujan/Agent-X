terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # Production Remote State with Locking
  # backend "gcs" {
  #   bucket = "agentx-tfstate-prod"
  #   prefix = "terraform/state/prod"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "prod_infrastructure" {
  source             = "../../"
  project_id         = var.project_id
  region             = var.region
  environment        = "prod"
  notification_email = var.notification_email
}

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # Remote State Storage in GCS (Uncomment in production pipeline)
  # backend "gcs" {
  #   bucket = "agentx-tfstate-dev"
  #   prefix = "terraform/state/dev"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "dev_infrastructure" {
  source             = "../../"
  project_id         = var.project_id
  region             = var.region
  environment        = "dev"
  notification_email = var.notification_email
}

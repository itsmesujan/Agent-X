# Secret Declarations (No plaintext values are stored in Terraform or Git)
resource "google_secret_manager_secret" "gemini_api_key" {
  project   = var.project_id
  secret_id = "agentx-gemini-api-key-${var.environment}"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    system      = "agent-x"
  }
}

resource "google_secret_manager_secret" "github_token" {
  project   = var.project_id
  secret_id = "agentx-github-token-${var.environment}"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    system      = "agent-x"
  }
}

resource "google_secret_manager_secret" "session_secret" {
  project   = var.project_id
  secret_id = "agentx-session-secret-${var.environment}"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    system      = "agent-x"
  }
}

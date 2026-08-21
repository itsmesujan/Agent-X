# Dead-Letter Topic (Provisioned first for dependency chaining)
resource "google_pubsub_topic" "dead_letter" {
  project                    = var.project_id
  name                       = "agentx-dead-letter-${var.environment}"
  message_retention_duration = var.message_retention_duration

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    system      = "agent-x"
  }
}

# Primary Mission Event Bus Topics
resource "google_pubsub_topic" "mission_events" {
  project                    = var.project_id
  name                       = "agentx-mission-events-${var.environment}"
  message_retention_duration = var.message_retention_duration

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    system      = "agent-x"
  }
}

resource "google_pubsub_topic" "task_events" {
  project                    = var.project_id
  name                       = "agentx-task-events-${var.environment}"
  message_retention_duration = var.message_retention_duration

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    system      = "agent-x"
  }
}

resource "google_pubsub_topic" "agent_events" {
  project                    = var.project_id
  name                       = "agentx-agent-events-${var.environment}"
  message_retention_duration = var.message_retention_duration

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    system      = "agent-x"
  }
}

resource "google_pubsub_topic" "recovery_events" {
  project                    = var.project_id
  name                       = "agentx-recovery-events-${var.environment}"
  message_retention_duration = var.message_retention_duration

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    system      = "agent-x"
  }
}

# Subscriptions with Dead Letter Policy
resource "google_pubsub_subscription" "task_worker_sub" {
  project              = var.project_id
  name                 = "agentx-task-worker-sub-${var.environment}"
  topic                = google_pubsub_topic.task_events.name
  ack_deadline_seconds = var.ack_deadline_seconds

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }

  expiration_policy {
    ttl = "" # Never expire
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "google_pubsub_subscription" "recovery_sub" {
  project              = var.project_id
  name                 = "agentx-recovery-sub-${var.environment}"
  topic                = google_pubsub_topic.recovery_events.name
  ack_deadline_seconds = 60

  expiration_policy {
    ttl = ""
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "google_pubsub_subscription" "dead_letter_sub" {
  project              = var.project_id
  name                 = "agentx-dead-letter-sub-${var.environment}"
  topic                = google_pubsub_topic.dead_letter.name
  ack_deadline_seconds = 300

  expiration_policy {
    ttl = ""
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

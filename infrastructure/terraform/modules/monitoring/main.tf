# 1. Alert Notification Channel
resource "google_monitoring_notification_channel" "email" {
  project      = var.project_id
  display_name = "Agent-X Ops Team (${var.environment})"
  type         = "email"

  labels = {
    email_address = var.notification_email
  }
}

# 2. Alert Policy: Cloud Run High HTTP 5xx Error Rate
resource "google_monitoring_alert_policy" "high_error_rate" {
  project      = var.project_id
  display_name = "Agent-X High 5xx Error Rate (${var.environment})"
  combiner     = "OR"

  conditions {
    display_name = "Cloud Run 5xx Responses > 5%"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]

  alert_strategy {
    auto_close = "1800s"
  }
}

# 3. Alert Policy: Dead Letter Queue Backlog Warning
resource "google_monitoring_alert_policy" "dlq_backlog" {
  project      = var.project_id
  display_name = "Agent-X Dead Letter Queue Message Spike (${var.environment})"
  combiner     = "OR"

  conditions {
    display_name = "Undeliverable Dead Letter Messages > 5"
    condition_threshold {
      filter          = "resource.type = \"pubsub_subscription\" AND metric.type = \"pubsub.googleapis.com/subscription/num_undelivered_messages\" AND resource.labels.subscription_id = \"agentx-dead-letter-sub-${var.environment}\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
}

# 4. Agent-X Operational Monitoring Dashboard
resource "google_monitoring_dashboard" "agentx_dashboard" {
  project        = var.project_id
  dashboard_json = jsonencode({
    displayName = "Agent-X Mission Operations (${var.environment})"
    gridLayout = {
      columns = 2
      widgets = [
        {
          title = "API Coordinator Request Volume & Latency"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\""
                    aggregation = {
                      alignmentPeriod = "60s"
                      perSeriesAligner = "ALIGN_RATE"
                    }
                  }
                }
              }
            ]
          }
        },
        {
          title = "Subagent Worker Memory Utilization"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/container/memory/utilizations\""
                    aggregation = {
                      alignmentPeriod = "60s"
                      perSeriesAligner = "ALIGN_MEAN"
                    }
                  }
                }
              }
            ]
          }
        }
      ]
    }
  })
}

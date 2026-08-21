output "mission_events_topic_id" {
  description = "Pub/Sub Topic ID for Mission Events"
  value       = google_pubsub_topic.mission_events.id
}

output "task_events_topic_id" {
  description = "Pub/Sub Topic ID for Task Events"
  value       = google_pubsub_topic.task_events.id
}

output "agent_events_topic_id" {
  description = "Pub/Sub Topic ID for Agent Events"
  value       = google_pubsub_topic.agent_events.id
}

output "recovery_events_topic_id" {
  description = "Pub/Sub Topic ID for Recovery Events"
  value       = google_pubsub_topic.recovery_events.id
}

output "dead_letter_topic_id" {
  description = "Pub/Sub Dead Letter Topic ID"
  value       = google_pubsub_topic.dead_letter.id
}

output "task_worker_subscription_id" {
  description = "Pub/Sub Subscription ID for Worker Task Ingestion"
  value       = google_pubsub_subscription.task_worker_sub.id
}

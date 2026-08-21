output "database_name" {
  description = "Name of the Firestore database"
  value       = google_firestore_database.database.name
}

output "database_id" {
  description = "Resource ID of the Firestore database"
  value       = google_firestore_database.database.id
}

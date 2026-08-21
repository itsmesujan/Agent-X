output "gemini_secret_id" {
  description = "Secret ID for Gemini API Key"
  value       = google_secret_manager_secret.gemini_api_key.id
}

output "gemini_secret_name" {
  description = "Resource name for Gemini API Key secret"
  value       = google_secret_manager_secret.gemini_api_key.name
}

output "github_token_secret_id" {
  description = "Secret ID for GitHub Token"
  value       = google_secret_manager_secret.github_token.id
}

output "session_secret_id" {
  description = "Secret ID for Session Encryption Secret"
  value       = google_secret_manager_secret.session_secret.id
}

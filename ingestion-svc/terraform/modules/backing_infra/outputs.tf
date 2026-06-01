output "service_account_email" {
  value       = google_service_account.ingestion_sa.email
  description = "The email of the created service account"
}

output "bucket_name" {
  value       = google_storage_bucket.workspace_bucket.name
  description = "The name of the workspace GCS bucket"
}

output "bucket_url" {
  value       = google_storage_bucket.workspace_bucket.url
  description = "The URL of the workspace GCS bucket"
}

output "db_instance_connection_name" {
  value       = google_sql_database_instance.db_instance.connection_name
  description = "The connection name of the Cloud SQL database instance"
}

output "db_instance_ip" {
  value       = google_sql_database_instance.db_instance.public_ip_address
  description = "The public IP address of the Cloud SQL database instance"
}

output "secret_id" {
  value       = google_secret_manager_secret.db_pass_secret.id
  description = "The secret ID in Secret Manager containing the database password"
}

resource "google_service_account" "ingestion_sa" {
  account_id   = "iw-ingestion-svc-sa-${var.environment}"
  display_name = "Service Account for InsightWave Ingestion Service (${var.environment})"
  project      = var.project_id
}

resource "google_storage_bucket" "workspace_bucket" {
  name                        = var.bucket_name
  location                    = var.region
  project                     = var.project_id
  force_destroy               = var.environment == "dev" ? true : false
  uniform_bucket_level_access = true

  public_access_prevention = "enforced"
}

resource "random_password" "db_password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "google_sql_database_instance" "db_instance" {
  name             = var.db_instance_name
  database_version = var.db_version
  region           = var.region
  project          = var.project_id

  settings {
    tier = var.db_tier

    ip_configuration {
      ipv4_enabled = true
    }

    backup_configuration {
      enabled = var.environment == "prod" ? true : false
    }
  }

  deletion_protection = var.environment == "prod" ? true : false
}

resource "google_sql_database" "postgres_db" {
  name     = "postgres"
  instance = google_sql_database_instance.db_instance.name
  project  = var.project_id
}

resource "google_sql_user" "postgres_user" {
  name     = "postgres"
  instance = google_sql_database_instance.db_instance.name
  password = random_password.db_password.result
  project  = var.project_id
}

resource "google_secret_manager_secret" "db_pass_secret" {
  secret_id = var.secret_name
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_pass_version" {
  secret      = google_secret_manager_secret.db_pass_secret.id
  secret_data = random_password.db_password.result
}

# IAM Permissions for Service Account
resource "google_storage_bucket_iam_member" "bucket_admin" {
  bucket = google_storage_bucket.workspace_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.ingestion_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  secret_id = google_secret_manager_secret.db_pass_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ingestion_sa.email}"
  project   = var.project_id
}

resource "google_project_iam_member" "sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.ingestion_sa.email}"
}

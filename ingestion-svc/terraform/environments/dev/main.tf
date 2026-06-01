terraform {
  required_version = ">= 1.0.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.0.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "backing_infra" {
  source = "../../modules/backing_infra"

  project_id       = var.project_id
  region           = var.region
  environment      = "dev"
  bucket_name      = "insight-wave-test-appmod-dev"
  db_instance_name = "iw-ingestion-svc-db-dev"
  db_tier          = "db-f1-micro"
  db_version       = "POSTGRES_15"
  secret_name      = "iw-ingestion-svc-dev-db-password"
}

output "dev_sa_email" {
  value = module.backing_infra.service_account_email
}

output "dev_bucket_name" {
  value = module.backing_infra.bucket_name
}

output "dev_db_connection" {
  value = module.backing_infra.db_instance_connection_name
}

output "dev_secret_id" {
  value = module.backing_infra.secret_id
}

variable "project_id" {
  type        = string
  description = "The GCP Project ID where resources will be created"
}

variable "environment" {
  type        = string
  description = "The environment name (e.g., dev, prod)"
}

variable "region" {
  type        = string
  description = "The region where resources will be created"
  default     = "us-central1"
}

variable "bucket_name" {
  type        = string
  description = "The name of the Google Cloud Storage bucket"
}

variable "db_instance_name" {
  type        = string
  description = "The name of the Cloud SQL database instance"
}

variable "db_tier" {
  type        = string
  description = "The tier/machine type for the Cloud SQL database instance"
  default     = "db-f1-micro"
}

variable "db_version" {
  type        = string
  description = "The PostgreSQL database version"
  default     = "POSTGRES_15"
}

variable "secret_name" {
  type        = string
  description = "The name of the Secret Manager secret for database password"
}

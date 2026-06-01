variable "project_id" {
  type        = string
  description = "The GCP Project ID for production"
}

variable "region" {
  type        = string
  description = "The GCP region for production"
  default     = "us-central1"
}

variable "project_id" {
  type        = string
  description = "The GCP Project ID for development"
}

variable "region" {
  type        = string
  description = "The GCP region for development"
  default     = "us-central1"
}

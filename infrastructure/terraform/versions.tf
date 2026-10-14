# ============================================================================
# Terraform + provider version constraints.
# Pinning versions keeps `terraform apply` reproducible across machines.
# ============================================================================
terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # NOTE: state is stored locally by default. For team use, configure a remote
  # backend (e.g. a GCS bucket) here so state is shared and locked. Example:
  #
  # backend "gcs" {
  #   bucket = "my-tf-state-bucket"
  #   prefix = "knowledge-assistant"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

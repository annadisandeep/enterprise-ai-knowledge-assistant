# ============================================================================
# Useful values surfaced after `terraform apply`.
# ============================================================================

output "backend_url" {
  description = "Public HTTPS URL of the backend Cloud Run service (API at /api)."
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  description = "Public HTTPS URL of the frontend Cloud Run service (the SPA)."
  value       = google_cloud_run_v2_service.frontend.uri
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository path for pushing/pulling images."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
}

output "chroma_bucket_name" {
  description = "GCS bucket backing the durable Chroma vector store."
  value       = google_storage_bucket.chroma.name
}

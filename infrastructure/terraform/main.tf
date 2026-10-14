# ============================================================================
# Main infrastructure for the Enterprise AI Knowledge Assistant on Cloud Run.
#
# What this builds:
#   - Enables the required Google Cloud APIs.
#   - An Artifact Registry Docker repo to hold the two images.
#   - A runtime service account for the backend (least privilege).
#   - Secret Manager secrets for API_KEY and GEMINI_API_KEY.
#   - A GCS bucket for DURABLE Chroma vector-store persistence.
#   - Two Cloud Run v2 services (backend API + frontend static site).
#   - Optional public (allUsers) invoker IAM on both services.
#
# Key design decisions (explained for future-you):
#   * Cloud Run's local filesystem is EPHEMERAL — anything written inside a
#     container is lost when the instance is replaced. The vector store must
#     survive restarts, so we mount a GCS bucket (via gcsfuse) at /app/data and
#     point CHROMA_PERSIST_DIR at /app/data/chroma.
#   * Secrets live in Secret Manager, not in env vars in the service YAML, so
#     they never appear in plaintext in the Cloud Run config or CI logs.
# ============================================================================

# ---- 1. Enable required APIs -----------------------------------------------
# Terraform will turn these on; without them the resources below fail to create.
locals {
  required_apis = [
    "run.googleapis.com",              # Cloud Run
    "artifactregistry.googleapis.com", # Artifact Registry (Docker images)
    "secretmanager.googleapis.com",    # Secret Manager
  ]
}

resource "google_project_service" "enabled" {
  for_each = toset(local.required_apis)
  project  = var.project_id
  service  = each.value

  # Leave the APIs enabled if this stack is destroyed; other things may use them.
  disable_on_destroy = false
}

# ---- 2. Artifact Registry (Docker) -----------------------------------------
resource "google_artifact_registry_repository" "images" {
  location      = var.region
  repository_id = var.repository_name
  description   = "Container images for the Knowledge Assistant (backend + frontend)."
  format        = "DOCKER"

  depends_on = [google_project_service.enabled]
}

# ---- 3. Backend runtime service account ------------------------------------
# The identity the backend Cloud Run service runs as. We grant it only what it
# needs: read its secrets and read/write its GCS bucket.
resource "google_service_account" "backend_runtime" {
  account_id   = "knowledge-backend-sa"
  display_name = "Knowledge Assistant backend runtime"
}

# ---- 4. Secrets -------------------------------------------------------------
# One secret per sensitive value. The actual value is added as a secret VERSION.
resource "google_secret_manager_secret" "api_key" {
  secret_id = "knowledge-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.enabled]
}

resource "google_secret_manager_secret_version" "api_key" {
  secret      = google_secret_manager_secret.api_key.id
  secret_data = var.api_key
}

resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "knowledge-gemini-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.enabled]
}

resource "google_secret_manager_secret_version" "gemini_api_key" {
  secret      = google_secret_manager_secret.gemini_api_key.id
  secret_data = var.gemini_api_key
}

# Let the backend SA read (only) these two secrets.
resource "google_secret_manager_secret_iam_member" "backend_api_key" {
  secret_id = google_secret_manager_secret.api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_gemini_key" {
  secret_id = google_secret_manager_secret.gemini_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_runtime.email}"
}

# ---- 5. Durable vector-store bucket ----------------------------------------
# Cloud Run mounts this bucket as a volume (gcsfuse) so Chroma's on-disk files
# persist across instance restarts and deploys.
#
# Caveat: gcsfuse is an object-store-backed filesystem, not a POSIX disk. It is
# fine for Chroma's persistence here, but for very high write throughput you
# would graduate to a managed vector DB or a Filestore/NFS mount. Documented so
# the tradeoff is explicit.
resource "google_storage_bucket" "chroma" {
  name                        = "${var.project_id}-knowledge-chroma"
  location                    = var.region
  force_destroy               = false # protect data: refuse to delete a non-empty bucket
  uniform_bucket_level_access = true

  # Keep a single live version of objects; gcsfuse manages its own layout.
  versioning {
    enabled = false
  }
}

# The backend SA needs read/write on the bucket to persist the vector store.
resource "google_storage_bucket_iam_member" "backend_chroma_rw" {
  bucket = google_storage_bucket.chroma.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.backend_runtime.email}"
}

# ---- 6. Backend Cloud Run service ------------------------------------------
resource "google_cloud_run_v2_service" "backend" {
  name     = "knowledge-backend"
  location = var.region

  # "all" = reachable from the public internet. Even when public, the app is
  # protected by its API_KEY (see access-model note at the bottom). Switch to
  # "internal-and-cloud-load-balancing" to keep it off the public internet.
  ingress = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.backend_runtime.email

    scaling {
      min_instance_count = var.backend_min_instances
      max_instance_count = var.backend_max_instances
    }

    # --- The GCS-backed volume for Chroma persistence ---
    volumes {
      name = "chroma-data"
      gcs {
        bucket    = google_storage_bucket.chroma.name
        read_only = false
      }
    }

    containers {
      image = var.backend_image

      # Cloud Run injects PORT=8080; the app reads it. Expose it explicitly.
      ports {
        container_port = 8080
      }

      # Mount the bucket at /app/data so CHROMA_PERSIST_DIR (/app/data/chroma)
      # lives on durable storage.
      volume_mounts {
        name       = "chroma-data"
        mount_path = "/app/data"
      }

      # Resource sizing:
      #  - The 'hashing' embedding backend is light (512Mi is plenty).
      #  - 'sentence-transformers' loads a torch model into memory and needs
      #    roughly 1-2Gi; 1Gi is the practical minimum. Bump memory to "2Gi"
      #    (and consider cpu = "2") if you see OOM kills with that backend.
      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      # --- Non-secret configuration ---
      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
      env {
        name  = "EMBEDDING_BACKEND"
        value = var.embedding_backend
      }
      env {
        name  = "LLM_PROVIDER"
        value = "gemini"
      }
      env {
        name  = "CHROMA_PERSIST_DIR"
        value = "/app/data/chroma"
      }
      env {
        name  = "CORS_ALLOW_ORIGINS"
        value = var.cors_allow_origins
      }

      # --- Secrets pulled from Secret Manager at runtime ---
      env {
        name = "API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.api_key.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_api_key.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  depends_on = [
    google_project_service.enabled,
    google_secret_manager_secret_iam_member.backend_api_key,
    google_secret_manager_secret_iam_member.backend_gemini_key,
    google_storage_bucket_iam_member.backend_chroma_rw,
  ]
}

# ---- 7. Frontend Cloud Run service -----------------------------------------
# A plain static site (nginx). No secrets, no volume. Public so browsers can
# load it.
resource "google_cloud_run_v2_service" "frontend" {
  name     = "knowledge-frontend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = var.frontend_min_instances
      max_instance_count = var.frontend_max_instances
    }

    containers {
      image = var.frontend_image

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
  }

  depends_on = [google_project_service.enabled]
}

# ---- 8. Invoker IAM (access model) -----------------------------------------
# ACCESS MODEL (default): both services are PUBLIC (allUsers may invoke), and
# the backend is PROTECTED BY THE APPLICATION'S API_KEY (the X-API-Key header on
# write endpoints). This is the simplest model for a public demo/portfolio: the
# frontend is a static site everyone can load, and the backend rejects
# unauthenticated writes at the app layer.
#
# TRADEOFF: "public + app API key" means the network endpoint is reachable by
# anyone; your protection is the shared key, so rotate it and keep it secret.
# For stronger isolation set allow_public_access = false, which removes the
# allUsers binding. Then callers need a Google identity with run.invoker — put
# the services behind an Identity-Aware Proxy / load balancer, or grant specific
# service accounts/users the invoker role instead of allUsers.
resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  count    = var.allow_public_access ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  count    = var.allow_public_access ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

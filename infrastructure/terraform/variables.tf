# ============================================================================
# Input variables. Real values go in a `terraform.tfvars` file that you create
# from terraform.tfvars.example. NEVER commit terraform.tfvars (it holds API
# keys). *.tfvars is gitignored — see the README.
# ============================================================================

variable "project_id" {
  description = "Google Cloud project ID to deploy into."
  type        = string
}

variable "region" {
  description = "Region for Cloud Run, Artifact Registry, and the GCS bucket."
  type        = string
  default     = "us-central1"
}

variable "repository_name" {
  description = "Artifact Registry (Docker) repository name that holds the images."
  type        = string
  default     = "knowledge-assistant"
}

# ---- Container images ------------------------------------------------------
# Full image references, including tag, e.g.
#   us-central1-docker.pkg.dev/<project>/<repo>/knowledge-backend:<tag>
# Build and push these with the deploy workflow (or locally) before applying,
# or apply once with placeholder images and let the deploy workflow swap them.
variable "backend_image" {
  description = "Fully-qualified backend container image (with tag)."
  type        = string
}

variable "frontend_image" {
  description = "Fully-qualified frontend container image (with tag)."
  type        = string
}

# ---- Application configuration ---------------------------------------------
variable "cors_allow_origins" {
  description = "Comma-separated allowed browser origins for the backend CORS policy (no spaces). Typically the frontend Cloud Run URL."
  type        = string
  default     = "*"
}

variable "embedding_backend" {
  description = "Embedding backend for the backend service: 'sentence-transformers' (semantic) or 'hashing' (fast/cheap, no model download)."
  type        = string
  default     = "sentence-transformers"
}

# ---- Secrets (sensitive) ---------------------------------------------------
# These are written into Secret Manager, not into the service definition.
variable "gemini_api_key" {
  description = "Gemini API key, stored in Secret Manager and injected into the backend at runtime."
  type        = string
  sensitive   = true
}

variable "api_key" {
  description = "Shared API key (X-API-Key) that protects the backend's write endpoints. Stored in Secret Manager."
  type        = string
  sensitive   = true
}

# ---- Access model ----------------------------------------------------------
variable "allow_public_access" {
  description = "If true, both Cloud Run services allow unauthenticated (allUsers) invocation. The backend is still protected by its application API key. Set false to require Google IAM auth on the invoker."
  type        = bool
  default     = true
}

# ---- Scaling ---------------------------------------------------------------
variable "backend_min_instances" {
  description = "Minimum backend instances. 0 = scale to zero (cheapest, but adds cold-start latency)."
  type        = number
  default     = 0
}

variable "backend_max_instances" {
  description = "Maximum backend instances (caps cost and concurrency)."
  type        = number
  default     = 3
}

variable "frontend_min_instances" {
  description = "Minimum frontend instances. 0 = scale to zero."
  type        = number
  default     = 0
}

variable "frontend_max_instances" {
  description = "Maximum frontend instances."
  type        = number
  default     = 3
}

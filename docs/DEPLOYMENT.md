# Deployment (Google Cloud)

This guide deploys the **Enterprise AI Knowledge Assistant** to **Google Cloud** using **Terraform** to provision:

- **Cloud Run** — runs the backend (and optionally the frontend) container, scales to zero.
- **Artifact Registry** — stores the Docker images.
- **Secret Manager** — holds `API_KEY` and `GEMINI_API_KEY`.
- **Cloud Storage (GCS) bucket** — durable storage for the Chroma vector DB and document registry (mounted into the stateless container).

> ⚠️ **Cost & approval warning.** These are **paid cloud resources**. Do **not** deploy without the account owner's approval. Keep `min_instances = 0`, set a **budget alert**, and run **`terraform destroy`** when finished to avoid ongoing charges. See [COST.md](COST.md).

> This is a **portfolio-grade** deployment. See the [storage tradeoff](#stateless-cloud-run--storage-tradeoff) and [SECURITY.md](SECURITY.md) for what a higher-scale, hardened deployment would add.

---

## Prerequisites

| Requirement | Notes |
| --- | --- |
| **GCP project** | With **billing enabled** |
| **gcloud CLI** | Authenticated: `gcloud auth login` and `gcloud auth application-default login` |
| **Terraform** | Recent 1.x |
| **Docker** | To build and push images |
| **A Gemini API key** | From [ai.google.dev](https://ai.google.dev) |
| **Owner approval** | Required before creating paid resources |

Set a few shell variables used throughout (adjust to your values):

```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export REPO="knowledge-assistant"          # Artifact Registry repo name
gcloud config set project "$PROJECT_ID"
```

---

## Step 1 — Enable required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com
```

---

## Step 2 — Create the Artifact Registry repository

(You can also let Terraform create it; if you build images before `terraform apply`, create it manually first.)

```bash
gcloud artifacts repositories create "$REPO" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Enterprise AI Knowledge Assistant images"

gcloud auth configure-docker "${REGION}-docker.pkg.dev"
```

---

## Step 3 — Build and push the images

Backend:

```bash
export BACKEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/backend:latest"

docker build -t "$BACKEND_IMAGE" ./backend
docker push "$BACKEND_IMAGE"
```

Frontend (if deploying the SPA as a container):

```bash
export FRONTEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/frontend:latest"

docker build -t "$FRONTEND_IMAGE" ./frontend
docker push "$FRONTEND_IMAGE"
```

> The backend container listens on **port 8080** (Cloud Run's expected default).

---

## Step 4 — Store secrets in Secret Manager

```bash
printf 'a-long-random-secret' | gcloud secrets create API_KEY --data-file=-
printf 'your-gemini-api-key'   | gcloud secrets create GEMINI_API_KEY --data-file=-
```

(To update later: `gcloud secrets versions add API_KEY --data-file=-`.)

Terraform wires these secrets into the Cloud Run service as environment variables, so the application reads `API_KEY` and `GEMINI_API_KEY` at runtime without baking them into the image.

---

## Step 5 — Configure Terraform

From `infrastructure/terraform/`, create a `terraform.tfvars` (names are illustrative — match them to the variables declared in the Terraform module):

```hcl
project_id      = "your-gcp-project-id"
region          = "us-central1"
repository      = "knowledge-assistant"
backend_image   = "us-central1-docker.pkg.dev/your-gcp-project-id/knowledge-assistant/backend:latest"
chroma_bucket   = "your-project-chroma-bucket"   # globally unique
min_instances   = 0                               # scale to zero — keep costs near $0
max_instances   = 2
```

> Inspect the actual variable names in `infrastructure/terraform/variables.tf` and set exactly those. Do not invent variables.

---

## Step 6 — Provision with Terraform

```bash
cd infrastructure/terraform
terraform init
terraform plan -out tfplan        # REVIEW the plan carefully
terraform apply tfplan
```

Terraform provisions the GCS bucket, grants the Cloud Run service account access to the bucket and secrets, and deploys the Cloud Run service with the GCS volume mounted at `CHROMA_PERSIST_DIR`.

After apply, Terraform outputs the Cloud Run **service URL**. Test it:

```bash
curl https://<your-cloud-run-url>/api/health
```

(Health is public. Protected endpoints require `X-API-Key: <your API_KEY>`.)

---

## Stateless Cloud Run + storage tradeoff

Cloud Run instances are **stateless and ephemeral**: local disk is wiped between instances, and instances don't share a filesystem. But the RAG app needs **durable** storage for Chroma vectors and the document registry.

**This design** mounts a **GCS bucket via gcsfuse** as the Chroma persistence directory, so data survives restarts and scale events.

**Honest tradeoff:**
- gcsfuse is **not** a high-throughput, strongly-consistent database. It is perfectly fine for a **single-instance demo**.
- For concurrent writers or higher scale, you would hit consistency and performance limits. **Recommended upgrade:** move to a **managed vector database** (hosted Chroma, `pgvector` on Cloud SQL, or a dedicated vector service) and a managed metadata store, and keep Cloud Run truly stateless.

This is documented plainly so reviewers understand the scope. See [ARCHITECTURE.md](ARCHITECTURE.md#design-decisions).

---

## GitHub Actions deploy workflow

`.github/workflows/deploy.yml` provides a **manual** deployment workflow (triggered on demand, e.g., `workflow_dispatch`). It builds the image, pushes it to Artifact Registry, and updates the Cloud Run service.

### Workload Identity Federation (no long-lived keys)

Rather than storing a service-account JSON key in GitHub secrets, the recommended approach is **Workload Identity Federation (WIF)**: GitHub Actions exchanges its OIDC token for short-lived GCP credentials. You configure a workload identity pool + provider and grant the GitHub repo's identity permission to deploy. This avoids long-lived secrets in CI and is the modern best practice.

> Because it's a **manual** workflow, deployments only happen when you explicitly trigger them — no accidental deploys on every push.

---

## Tearing it down (important)

To stop all charges, destroy everything Terraform created:

```bash
cd infrastructure/terraform
terraform destroy
```

Also consider deleting the Artifact Registry images and the GCS bucket if they aren't managed by Terraform, and removing secrets you no longer need.

---

## Deployment checklist

- [ ] Owner approval obtained for paid resources
- [ ] Budget alert configured in GCP Billing
- [ ] `min_instances = 0` (scale to zero)
- [ ] `API_KEY` and `GEMINI_API_KEY` stored in Secret Manager (not in images)
- [ ] `CORS_ALLOW_ORIGINS` set to your real frontend origin (no `*`)
- [ ] `ENVIRONMENT=production`
- [ ] Verified `/api/health` responds
- [ ] Plan to run `terraform destroy` when done

---

## Related docs

- [COST.md](COST.md) — keeping the bill near zero
- [SECURITY.md](SECURITY.md) — what hardening a real deployment needs
- [CONFIGURATION.md](CONFIGURATION.md) — the env vars Cloud Run injects
- [ARCHITECTURE.md](ARCHITECTURE.md) — the GCP topology

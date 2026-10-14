# Infrastructure (Terraform) — Knowledge Assistant on Cloud Run

This directory provisions the Google Cloud infrastructure for the Enterprise AI
Knowledge Assistant: two Cloud Run services (backend API + frontend SPA), an
Artifact Registry repo for images, Secret Manager secrets, and a GCS bucket that
gives the Chroma vector store durable storage.

## What gets created

- **APIs enabled**: Cloud Run, Artifact Registry, Secret Manager.
- **Artifact Registry** (Docker) repository for the two images.
- **Service account** for the backend runtime (least privilege).
- **Secret Manager** secrets for `API_KEY` and `GEMINI_API_KEY`.
- **GCS bucket** mounted into the backend at `/app/data` so Chroma persists
  across restarts (Cloud Run's own filesystem is ephemeral).
- **Cloud Run v2** services: `knowledge-backend` and `knowledge-frontend`.
- **Invoker IAM**: optional public (`allUsers`) access, toggled by a variable.

## Prerequisites

- Terraform >= 1.5 and the `gcloud` CLI, authenticated:
  `gcloud auth application-default login`
- A Google Cloud project with billing enabled.
- The two container images pushed to Artifact Registry (or apply once with
  placeholder image tags, then let the deploy workflow push and roll real ones).

## Usage

```bash
cd infrastructure/terraform

# 1. Create your real variables file from the example and edit it.
cp terraform.tfvars.example terraform.tfvars
#    -> fill in project_id, images, gemini_api_key, api_key, etc.

# 2. Initialise and review the plan.
terraform init
terraform plan

# 3. Apply.
terraform apply
```

Outputs include the backend URL, frontend URL, Artifact Registry path, and the
Chroma bucket name.

## Security notes

- **`terraform.tfvars` holds secrets — never commit it.** `*.tfvars` is
  gitignored here (see `.gitignore`), with `*.tfvars.example` allowed. Run
  `git status` before committing to be sure.
- Secrets are stored in **Secret Manager** and injected into Cloud Run at
  runtime via `secret_key_ref`, so they never appear in the service config or in
  CI logs.
- **Access model**: by default both services are public (`allow_public_access =
  true`). The backend is still protected by its application `API_KEY`
  (`X-API-Key` header). Set `allow_public_access = false` to require Google IAM
  auth on the invoker instead, and front the services with IAP / a load balancer
  or grant `run.invoker` to specific identities.

## Design decisions worth knowing

- **Why a GCS bucket?** Cloud Run instances have an ephemeral filesystem; any
  data written inside a container disappears when the instance is replaced. The
  bucket is mounted (gcsfuse) at `/app/data`, and `CHROMA_PERSIST_DIR` points at
  `/app/data/chroma`, so the vector index survives restarts and deploys. For
  very high write throughput you would move to a managed vector DB or NFS.
- **Memory sizing**: the `hashing` embedding backend is light. The
  `sentence-transformers` backend loads a torch model and needs ~1–2Gi — the
  backend defaults to 1Gi; raise `memory` to `2Gi` in `main.tf` if you hit OOM.
- **Scale to zero**: `min_instances = 0` keeps idle cost at zero at the price of
  cold-start latency. Set a minimum of 1 for a warm backend.

## Related

- `../../.github/workflows/deploy.yml` builds/pushes images and rolls out new
  revisions to the services created here (manual `workflow_dispatch`).
- `../../docker-compose.yml` runs the same stack locally for development.

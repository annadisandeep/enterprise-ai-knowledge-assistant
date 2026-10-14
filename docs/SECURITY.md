# Security

This document describes the security controls that **are implemented** in the Enterprise AI Knowledge Assistant and — just as importantly — the **limitations** that mean it is **not** a certified enterprise-ready product. Honesty here is part of the portfolio: knowing what you haven't done is as valuable as what you have.

---

## Implemented controls

### Configuration & secrets
- **Environment-based configuration** — no hardcoded secrets anywhere in the code. All config comes from environment variables / `.env` (local) or Secret Manager (GCP).
- **Secrets in Secret Manager** for deployed environments; never baked into images.

### Authentication
- **API-key authentication** for deployed environments via the `X-API-Key` header.
- **Constant-time comparison** of the key to avoid timing side-channels.
- Auth is **enforced only when `API_KEY` is set**; in local dev with no key, auth is disabled and a **startup warning is logged** so it's never silently off in production.
- **Health endpoint is always public** (no secret required for liveness/monitoring).

### Network / browser
- **Configurable CORS** via `CORS_ALLOW_ORIGINS` — **no wildcard in production**.
- **Credentials disabled** on CORS; authentication is **header-based** (`X-API-Key`), not cookie-based, which sidesteps a class of CSRF concerns.

### Upload safety
- **Size validation** (`MAX_UPLOAD_BYTES`, default 10 MB) → `413` when exceeded.
- **Type/extension validation** (`ALLOWED_EXTENSIONS`).
- **Magic-byte validation** for PDFs (`%PDF-`) so a renamed file can't masquerade as a PDF.
- **Binary-content rejection** for text uploads (refuses files that look binary).
- **Duplicate detection** via **SHA-256** → `409`, preventing redundant/poisoned re-ingestion of identical content.

### RAG / prompt-injection defenses
- **Retrieved context treated as untrusted data** — the system instruction forbids following any instructions embedded inside documents.
- **Context wrapped in delimiters** so the model distinguishes instructions from content.
- **Citations derived from retrieval, not model output** — the model **cannot fabricate** sources.
- **Explicit no-answer fallback** — if nothing relevant is retrieved, the app returns an honest "not found" rather than guessing, and does not call the LLM.
- **Low temperature + bounded output** (`LLM_TEMPERATURE`, `LLM_MAX_OUTPUT_TOKENS`) reduce off-script behavior.
- **Context/token limits** (`MAX_CONTEXT_CHARS`) bound what is sent to the model.

### Output handling
- **Sanitized error messages** — errors are safe and do not leak internals or stack traces.
- **Sanitized Markdown rendering** on the frontend — answers are rendered as sanitized Markdown, limiting injected-content impact in the browser.

### Supply chain & runtime
- **Non-root Docker** containers.
- **Dependency scanning in CI** — `pip-audit` (Python) and `npm audit` (JS).

#### Known dependency advisories (triaged, not ignored)

The audit tooling currently reports advisories that are **non-blocking in CI by
design** (`continue-on-error: true`), because they are triaged as low practical
risk for this project:

- **`transformers` (transitive via `sentence-transformers`)** — multiple advisories,
  nearly all concerning the loading of **untrusted models/configs** (unsafe
  deserialization, tokenizer ReDoS, etc.). This app **only loads one fixed, trusted
  model** (`all-MiniLM-L6-v2`) and **never loads user-supplied models**, so these
  are not reachable in our usage. Mitigation path: bump `transformers` as
  `sentence-transformers` compatibility allows, or switch the production image to
  the `hashing` embedding backend (which needs neither `torch` nor `transformers`).
- **Frontend dev tooling (`vite`/`esbuild`/`vitest`/`tinypool`)** — these are
  **devDependencies only**. They are **not part of the shipped artifact** (the
  production image is the static `dist/` bundle served by nginx), so they do not
  run in production. Fixes require major-version bumps and are tracked separately
  to avoid destabilizing the build.

The honest takeaway: these should be reviewed and updated on a schedule; they are
surfaced (not hidden) and reasoned about, rather than silently suppressed.

---

## Limitations (stated plainly)

This project is a **production-oriented portfolio demo**, not a hardened multi-tenant SaaS. The following are **known gaps**:

| Area | Limitation |
| --- | --- |
| **Authentication** | A **single shared API key** — there is **no per-user authentication, no RBAC, and no user identity**. Anyone with the key has full access. |
| **Multi-tenancy** | There is **one shared knowledge base**. **All uploaded documents are visible to every authenticated caller** — there is **no per-user or per-tenant document isolation / ACLs**. Do not upload documents that shouldn't be shared across all users of the instance. |
| **Prompt injection** | Mitigations **reduce but do not eliminate** risk. Prompt injection is an unsolved problem; a determined adversarial document could still influence outputs. |
| **Rate limiting** | **No application-layer rate limiting.** Abuse protection should be added at the edge (API gateway / **Cloud Armor** / a WAF). |
| **In-process model execution** | Embeddings and (for the hashing backend) similarity run **in the app process**. No isolation/sandboxing of model execution. |
| **Encryption at rest** | Chroma data is **not encrypted at the application layer**; it relies on the underlying **GCS/disk encryption**. No field-level or app-managed encryption. |
| **Audit logging** | **No structured audit log of queries** beyond application logs to stdout. No tamper-evident trail. |
| **Secret delivery to SPA** | `VITE_API_KEY` is inlined into the frontend bundle at build time — a key shipped to the browser is exposed. A real deployment should use a backend-for-frontend or gateway instead. |

---

## This is NOT certified enterprise-ready

Despite the name, treat this as a **demonstration of production-oriented engineering**, not a product you would place in front of real sensitive data without further work.

### What it would take to get there

- **SSO / OIDC** identity (e.g., Google, Okta, Entra ID) with real user accounts.
- **Per-user document ACLs** and **multi-tenant isolation** so users only see their own documents.
- **Role-based access control (RBAC)**.
- **Rate limiting** and **a WAF** (Cloud Armor) in front of the service.
- A managed, access-controlled **vector database** rather than file-backed Chroma.
- **Secrets rotation** policy and automation.
- **Audit logging** with retention and tamper resistance.
- **DLP** (data loss prevention) scanning on uploads and outputs.
- A professional **penetration test** and threat model review.
- Encryption and key management aligned to a compliance regime (e.g., CMEK).

---

## Reporting a concern

This is a personal portfolio project. If you spot an issue, open an issue on the repository: [github.com/annadisandeep/enterprise-ai-knowledge-assistant](https://github.com/annadisandeep/enterprise-ai-knowledge-assistant).

---

## Related docs

- [RAG.md](RAG.md#prompt-injection-defenses) — the prompt-injection defenses in detail
- [DEPLOYMENT.md](DEPLOYMENT.md) — WIF, secrets, and the storage tradeoff
- [CONFIGURATION.md](CONFIGURATION.md) — auth and CORS settings

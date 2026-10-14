# Configuration

Every tunable in the **Enterprise AI Knowledge Assistant** is an environment variable, loaded by the backend through a single Pydantic-settings object (see `app/core/config.py`) and by the frontend through Vite's `VITE_*` convention. Nothing sensitive is hardcoded.

- Backend variables live in `backend/.env` (copy from `backend/.env.example`).
- Frontend variables live in `frontend/.env.local` (or your hosting provider's env config).

> **Never commit a real `.env`.** Secrets belong in Secret Manager for deployed environments — see [DEPLOYMENT.md](DEPLOYMENT.md).

---

## Backend environment variables

### General

| Variable | Default | Required | Description |
| --- | --- | --- | --- |
| `ENVIRONMENT` | `development` | No | One of `development`, `staging`, `production`. Influences defaults and logged warnings. |
| `LOG_LEVEL` | `INFO` | No | Standard Python log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

### API security

| Variable | Default | Required | Description |
| --- | --- | --- | --- |
| `API_KEY` | _(empty)_ | **Yes in production** | Shared secret required as the `X-API-Key` header on protected endpoints. If empty, auth is **disabled** and a startup warning is logged (local dev only). |
| `CORS_ALLOW_ORIGINS` | `http://localhost:5173,http://localhost:3000` | No | Comma-separated allowed browser origins (no spaces). **Never use `*` in production.** |

### Uploads

| Variable | Default | Required | Description |
| --- | --- | --- | --- |
| `MAX_UPLOAD_BYTES` | `10485760` (10 MB) | No | Maximum accepted upload size. Larger files return `413`. |
| `ALLOWED_EXTENSIONS` | `.pdf,.txt,.md,.markdown` | No | Comma-separated allowed file extensions. |

### Embeddings

| Variable | Default | Required | Description |
| --- | --- | --- | --- |
| `EMBEDDING_BACKEND` | `sentence-transformers` | No | `sentence-transformers` (semantic) or `hashing` (fast deterministic fallback). See [below](#embedding-backends). |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | No | Model name for the sentence-transformers backend. |
| `EMBEDDING_DIM` | `384` | No | Vector dimensionality. Must match the backend's output (both produce 384). |

### Vector store

| Variable | Default | Required | Description |
| --- | --- | --- | --- |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | No | Directory where Chroma persists vectors. In GCP this points at a GCS-backed volume. |
| `CHROMA_COLLECTION` | `knowledge_base` | No | Name of the Chroma collection. |

### Chunking

| Variable | Default | Required | Description |
| --- | --- | --- | --- |
| `CHUNK_SIZE` | `1000` | No | Target chunk length in characters. |
| `CHUNK_OVERLAP` | `150` | No | Characters of overlap between consecutive chunks (preserves context at boundaries). |

### Retrieval / RAG

| Variable | Default | Required | Description |
| --- | --- | --- | --- |
| `RETRIEVAL_TOP_K` | `4` | No | Default number of chunks retrieved per query (overridable per request via `top_k`, 1–20). |
| `MIN_SIMILARITY` | `0.15` | No | Minimum cosine similarity for a chunk to be used. Below this, chunks are dropped; if none qualify, the app returns an explicit no-answer. |
| `MAX_CONTEXT_CHARS` | `8000` | No | Character budget for the assembled context sent to the LLM. |

### LLM provider

| Variable | Default | Required | Description |
| --- | --- | --- | --- |
| `LLM_PROVIDER` | `gemini` | No | `gemini` (real) or `mock` (deterministic, no network). See [below](#llm-providers). |
| `GEMINI_API_KEY` | _(empty)_ | **Yes when `LLM_PROVIDER=gemini`** | API key for Google Gemini. Get one free at [ai.google.dev](https://ai.google.dev). |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | No | Gemini model id. Override to any model your key can access (e.g. `gemini-3.8-flash`). The old `gemini-2.5-flash` default was retired for new API users. |
| `LLM_TEMPERATURE` | `0.2` | No | Sampling temperature. Low = more deterministic, grounded answers. |
| `LLM_MAX_OUTPUT_TOKENS` | `1024` | No | Maximum tokens in the generated answer. |
| `LLM_TIMEOUT_SECONDS` | `30` | No | Request timeout for the LLM call. Exceeding it returns `504`. |

---

## Frontend environment variables

| Variable | Default | Required | Description |
| --- | --- | --- | --- |
| `VITE_API_BASE_URL` | `/api` in prod, `http://localhost:8000/api` in local dev | No | Base URL the SPA uses to reach the backend. |
| `VITE_API_KEY` | _(empty)_ | Only if the backend has `API_KEY` set | Sent as `X-API-Key` so the SPA can call a protected API. Leave unset when backend auth is disabled. |

> Vite inlines `VITE_*` variables **at build time**. A value baked into a public SPA is visible to anyone with the page. For a real deployment, prefer a backend-for-frontend or a gateway rather than shipping a privileged key to the browser. See [SECURITY.md](SECURITY.md).

---

## Embedding backends

| Backend | Pros | Cons | Typical use |
| --- | --- | --- | --- |
| `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dim) | Real semantic similarity; good retrieval quality | Large dependency (torch); one-time model download | Production / realistic demos |
| `hashing` (deterministic lexical, 384-dim) | Instant, no download, no GPU, fully reproducible | Lexical only — no semantic understanding | CI, tests, fast local iteration |

Both are normalized so cosine similarity is comparable. Switch with `EMBEDDING_BACKEND`. If you change backends after indexing documents, re-ingest so vectors are consistent.

---

## LLM providers

| Provider | Behavior | Needs a key? |
| --- | --- | --- |
| `gemini` | Calls the configured model (default `gemini-3.5-flash-lite`) via the `google-genai` SDK with your temperature/timeout/token settings | Yes (`GEMINI_API_KEY`) |
| `mock` | Returns a deterministic, canned answer without any network call | No |

Use `mock` for offline development and automated tests; use `gemini` for real answers.

---

## How to get a free Gemini API key

1. Go to **[ai.google.dev](https://ai.google.dev)** (Google AI Studio).
2. Sign in with a Google account and open **Get API key**.
3. Create a key and copy it.
4. Put it in `backend/.env` as `GEMINI_API_KEY=...` (local), or store it in **Secret Manager** for GCP (see [DEPLOYMENT.md](DEPLOYMENT.md)).

The default `gemini-3.5-flash-lite` model has a generous free tier via Google AI Studio. Model availability and limits change over time — if a model returns a "no longer available" error, set `GEMINI_MODEL` to a current one your key can access. Always check the current quotas and pricing on the official site. See [COST.md](COST.md).

---

## Minimal `.env` recipes

**Zero-cost offline dev (no key, no ML download):**
```dotenv
EMBEDDING_BACKEND=hashing
LLM_PROVIDER=mock
```

**Realistic local dev with Gemini:**
```dotenv
EMBEDDING_BACKEND=sentence-transformers
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
```

**Production-like (auth on, strict CORS):**
```dotenv
ENVIRONMENT=production
API_KEY=a-long-random-secret
CORS_ALLOW_ORIGINS=https://your-frontend.example.com
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
```

# API Reference

Base path: **`/api`** (all responses are JSON). Interactive docs are available at **`/docs`** (Swagger UI) when the backend is running.

Local base URL examples:
- Local `uvicorn`: `http://localhost:8000`
- Docker Compose: `http://localhost:8080`

---

## Authentication

Protected endpoints require the header **`X-API-Key: <key>`** — but **only when the backend has `API_KEY` set**.

| Environment | `API_KEY` set? | Auth behavior |
| --- | --- | --- |
| Local dev | No | Auth **disabled**; a startup warning is logged. Any caller is allowed. |
| Deployed / configured | Yes | `X-API-Key` **required** on protected endpoints; compared in constant time. |

| Endpoint | Auth |
| --- | --- |
| `GET /` | Public |
| `GET /api/health` | **Always public** (unauthenticated) |
| `POST /api/documents` | Protected |
| `GET /api/documents` | Protected |
| `DELETE /api/documents/{id}` | Protected |
| `POST /api/chat` | Protected |

> "Protected" means the header is required **only when `API_KEY` is configured**. With no `API_KEY` (local dev), these endpoints are open.

---

## `GET /` — Liveness

Simple liveness probe.

**Response `200`:**
```json
{ "status": "ok", "service": "enterprise-ai-knowledge-assistant", "version": "1.0.0" }
```

```bash
curl http://localhost:8000/
```

---

## `GET /api/health` — Health & status

Unauthenticated. Reports runtime status and which backends are active.

**Response `200`:**
```json
{
  "status": "ok",
  "app": "Enterprise AI Knowledge Assistant",
  "version": "1.0.0",
  "environment": "development",
  "embedding_backend": "sentence-transformers",
  "llm_provider": "gemini",
  "document_count": 3
}
```

```bash
curl http://localhost:8000/api/health
```

---

## `POST /api/documents` — Upload a document

Uploads and ingests a document (extract → chunk → embed → index → register).

- **Content type:** `multipart/form-data`
- **Form field:** `file` (the document)
- **Allowed types:** `.pdf`, `.txt`, `.md`, `.markdown`
- **Max size:** `MAX_UPLOAD_BYTES` (default 10 MB)

**Request (curl):**
```bash
curl -X POST http://localhost:8000/api/documents \
  -H "X-API-Key: $API_KEY" \
  -F "file=@sample-data/acme-pto-benefits.md"
```

**Response `201`:**
```json
{
  "document": {
    "id": "a1b2c3d4",
    "filename": "acme-pto-benefits.md",
    "content_type": "text/markdown",
    "size_bytes": 4096,
    "char_count": 3980,
    "chunk_count": 5,
    "sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
    "uploaded_at": "2026-10-14T12:00:00Z"
  },
  "message": "Document ingested successfully."
}
```

**Errors:**

| Code | Meaning |
| --- | --- |
| `422` | Invalid, empty, or unsupported file (bad extension, empty content, binary content in a text file, failed magic-byte check) |
| `409` | Duplicate — a document with the same SHA-256 already exists |
| `413` | File too large (exceeds `MAX_UPLOAD_BYTES`) |
| `401` / `403` | Missing or invalid `X-API-Key` (when auth enabled) |

---

## `GET /api/documents` — List documents

Returns all ingested documents and a total count.

**Request:**
```bash
curl http://localhost:8000/api/documents -H "X-API-Key: $API_KEY"
```

**Response `200`:**
```json
{
  "documents": [
    {
      "id": "a1b2c3d4",
      "filename": "acme-pto-benefits.md",
      "content_type": "text/markdown",
      "size_bytes": 4096,
      "char_count": 3980,
      "chunk_count": 5,
      "sha256": "9f86d081…",
      "uploaded_at": "2026-10-14T12:00:00Z"
    }
  ],
  "total": 1
}
```

---

## `DELETE /api/documents/{id}` — Delete a document

Removes a document and all of its chunks from the vector store and registry.

**Request:**
```bash
curl -X DELETE http://localhost:8000/api/documents/a1b2c3d4 -H "X-API-Key: $API_KEY"
```

**Response `200`:**
```json
{ "id": "a1b2c3d4", "deleted_chunks": 5, "message": "Document deleted." }
```

**Errors:**

| Code | Meaning |
| --- | --- |
| `404` | No document with that id |
| `401` / `403` | Missing or invalid `X-API-Key` (when auth enabled) |

---

## `POST /api/chat` — Ask a question

Runs the RAG pipeline and returns a grounded answer with citations.

- **Content type:** `application/json`

**Request body:**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `question` | string | Yes | The user's question. Must be non-empty. |
| `top_k` | number | No | How many chunks to retrieve (1–20). Defaults to `RETRIEVAL_TOP_K` (4). |
| `document_id` | string | No | Restrict retrieval to a single document. |

**Request (curl):**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "question": "How many PTO days do employees get?", "top_k": 4 }'
```

**Response `200`:**
```json
{
  "answer": "Full-time employees accrue 20 days of paid time off per year.",
  "citations": [
    {
      "document_id": "a1b2c3d4",
      "filename": "acme-pto-benefits.md",
      "chunk_id": "a1b2c3d4-3",
      "chunk_index": 3,
      "similarity": 0.72,
      "snippet": "Full-time employees accrue 20 days of paid time off…"
    }
  ],
  "grounded": true,
  "model": "gemini-3.5-flash-lite",
  "used_fallback": false
}
```

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| `answer` | string | The generated answer (or an explicit no-answer message). |
| `citations` | array | Sources derived from retrieval — each has `document_id`, `filename`, `chunk_id`, `chunk_index`, `similarity`, `snippet`. Never fabricated by the model. |
| `grounded` | boolean | `true` if the answer is backed by retrieved context; `false` for no-answer cases. |
| `model` | string | The model/provider used (e.g., `gemini-3.5-flash-lite` or the mock). |
| `used_fallback` | boolean | Whether a fallback path was used. |

**Errors:**

| Code | Meaning |
| --- | --- |
| `422` | Empty question |
| `503` | Missing or invalid AI credentials |
| `504` | LLM request timed out (`LLM_TIMEOUT_SECONDS`) |
| `429` | Provider quota exceeded |
| `502` | Other upstream provider error |
| `401` / `403` | Missing or invalid `X-API-Key` (when auth enabled) |

---

## Error response shape

Errors are returned with the appropriate HTTP status and a **safe, sanitized** JSON message — internal details are not leaked. Example:

```json
{ "detail": "Unsupported file type. Allowed: .pdf, .txt, .md, .markdown" }
```

---

## Notes for frontend callers

- The SPA sets the `X-API-Key` header from `VITE_API_KEY` when it is configured.
- CORS is restricted to origins in `CORS_ALLOW_ORIGINS`; credentials are disabled (auth is header-based). See [CONFIGURATION.md](CONFIGURATION.md) and [SECURITY.md](SECURITY.md).

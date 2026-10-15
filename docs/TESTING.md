# Testing

The project is tested on both ends: **pytest** for the FastAPI backend and **vitest + Testing Library** for the React frontend. Tests are designed to run **fast, offline, and deterministically** by default — no Gemini key and no large model download required.

---

## Philosophy: mock the external AI

Automated tests should be **fast, free, and reproducible**. Real AI calls are none of those — they cost money, need network and credentials, and return non-deterministic text. So the default test configuration uses:

- **`EMBEDDING_BACKEND=hashing`** — a deterministic lexical embedder, no torch, no model download.
- **`LLM_PROVIDER=mock`** — a canned, deterministic LLM response, no network.

This lets CI validate the **entire pipeline and contract** (upload, extraction, chunking, retrieval, citation assembly, error handling, auth) without ever touching Google's servers. The one test that genuinely needs the semantic model **auto-skips** when it isn't available (see below).

---

## Backend tests (pytest)

**Current result (2026-10-15, CI configuration):** 67 passed, 0 skipped in about 40 s. The two semantic evaluation tests ran because sentence-transformers is installed locally; they auto-skip in the slim CI environment.

### Run them

```bash
cd backend
# activate your venv first (see SETUP.md)
pytest
```

With coverage:

```bash
pytest --cov=app --cov-report=term-missing
# HTML report:
pytest --cov=app --cov-report=html   # open htmlcov/index.html
```

Run a subset:

```bash
pytest -k "upload or citation"       # by keyword
pytest tests/test_chat_api.py        # a single file
pytest -v                            # verbose
```

> CI runs with the hashing + mock configuration by default, so a plain `pytest` mirrors CI. To exercise the real semantic path locally, install the full deps and set `EMBEDDING_BACKEND=sentence-transformers`.

### What's covered

| Area | What is verified |
| --- | --- |
| **Health** | `/api/health` returns status and reports the active embedding backend, LLM provider, and document count |
| **Upload validation** | Size limits (`413`), extension/type checks and empty/binary content (`422`), duplicate SHA-256 (`409`) |
| **Extraction** | PDF text extraction (PyMuPDF), text decoding, magic-byte (`%PDF-`) checks, binary rejection |
| **Chunking** | Boundary-aware splitting, chunk sizes and overlap behavior |
| **Embeddings** | Both backends produce 384-dim normalized vectors; determinism of the hashing backend |
| **Retrieval** | Top-k search, cosine similarity (`1 - distance`), `MIN_SIMILARITY` filtering, per-document scoping |
| **Deletion** | Chunks removed from the vector store and registry; `404` for unknown ids |
| **Citation integrity** | Citations are built from retrieved chunks and correspond to real sources — never fabricated |
| **No-answer** | When nothing clears the similarity threshold, an explicit no-answer with `grounded: false` is returned (LLM not called) |
| **Missing credentials** | Gemini provider without a valid key surfaces as `503` |
| **LLM failures** | Timeout → `504`, quota → `429`, other provider error → `502` |
| **Prompt injection** | Document content framed as untrusted data; citations can't be forged through injected text |
| **API auth** | With `API_KEY` set, protected endpoints require a valid `X-API-Key`; health stays public |
| **Semantic eval** | Retrieval quality over the synthetic evaluation set (skips when the model is unavailable — see below) |
| **Configuration** | Default Gemini model id (`gemini-3.5-flash-lite`), override via env, provider selection |

Per-file counts: `test_extraction` 10, `test_rag_engine` 8, `test_chat_api` 7, `test_auth` 6, `test_chunking` 6, `test_documents_api` 6, `test_llm_provider` 6, `test_config` 5, `test_embeddings` 5, `test_retrieval` 4, `test_eval` 2, `test_health` 2.

---

## The semantic evaluation test

`sample-data/evaluation-set.json` contains synthetic question → expected-source pairs over the sample ACME documents.

The evaluation test:
1. Ingests the sample documents using the **real** `sentence-transformers` backend.
2. Runs each evaluation question through retrieval.
3. Asserts that the expected source document(s) appear in the retrieved results.

Because this requires the heavy `sentence-transformers` dependency and the `all-MiniLM-L6-v2` model, the test **automatically skips** when the library or model isn't available (e.g., in the fast CI configuration using the hashing backend). This keeps the default suite quick and green while still providing a real semantic-quality check when you run the full stack.

To run it locally, install the full requirements and ensure the model can download:

```bash
cd backend
pip install -r requirements-dev.txt
EMBEDDING_BACKEND=sentence-transformers pytest -k eval
```

---

## Frontend tests (vitest + Testing Library)

**Current result (2026-10-15):** 13 passed across 5 files (`ChatMessage`, `ChatPanel`, `Citations`, `UploadDropzone`, `utils`).

```bash
cd frontend
npm install        # first time
npm run test       # vitest
npm run lint       # ESLint
```

Coverage (if configured in the Vitest setup):

```bash
npm run test -- --coverage
```

Frontend tests use **vitest** with **React Testing Library** to verify component rendering and behavior — for example, that answers render as sanitized Markdown and that citations are displayed. They do not call a real backend.

---

## Continuous integration

GitHub Actions (`.github/workflows/ci.yml`) runs the backend and frontend test suites on push/PR using the fast hashing + mock configuration, and also runs **dependency scanning** (`pip-audit`, `npm audit`). See [DEPLOYMENT.md](DEPLOYMENT.md) for the deploy workflow.

---

## Related docs

- [SETUP.md](SETUP.md) — getting the environments running
- [CONFIGURATION.md](CONFIGURATION.md) — the `hashing`/`mock` settings
- [RAG.md](RAG.md) — what the retrieval tests are checking

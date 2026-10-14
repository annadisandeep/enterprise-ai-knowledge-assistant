# Local Development Setup

This guide walks you through running the **Enterprise AI Knowledge Assistant** on your own machine — backend, frontend, and the optional Docker Compose path — on **Windows (PowerShell)** and **macOS/Linux**.

New to the project? Read the [README](../README.md) first for the big picture.

---

## Prerequisites

| Tool | Version | Notes |
| --- | --- | --- |
| **Python** | 3.12 recommended (3.11 works) | For the FastAPI backend |
| **Node.js** | 20+ | For the React/Vite frontend (includes `npm`) |
| **Docker** | Latest (optional) | Only needed for the `docker compose` path |
| **Git** | Any recent | To clone the repo |
| **Gemini API key** | Free tier | Optional for local dev — you can use `LLM_PROVIDER=mock` instead. Get one at [ai.google.dev](https://ai.google.dev) |

> **Tip:** You can run the entire app locally with **no API key and no heavy ML downloads** by using the fast mode described below (`EMBEDDING_BACKEND=hashing`, `LLM_PROVIDER=mock`).

---

## 1. Clone the repository

```bash
git clone https://github.com/annadisandeep/enterprise-ai-knowledge-assistant.git
cd enterprise-ai-knowledge-assistant
```

---

## 2. Backend setup

### Windows (PowerShell)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate

pip install -r requirements-dev.txt
Copy-Item .env.example .env       # then edit .env as needed
uvicorn app.main:app --reload --port 8000
```

### macOS / Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements-dev.txt
cp .env.example .env               # then edit .env as needed
uvicorn app.main:app --reload --port 8000
```

Once running:

- API base: `http://localhost:8000`
- Interactive docs (Swagger UI): `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### Fast mode (recommended for first run / CI)

Heavy ML dependencies (torch, sentence-transformers) are large and the model downloads on first use. To skip all of that and avoid needing a Gemini key, set these in your `.env`:

```dotenv
EMBEDDING_BACKEND=hashing
LLM_PROVIDER=mock
```

This uses the deterministic lexical embedder and a canned LLM response — perfect for verifying the app runs end-to-end before investing in the full semantic stack.

### Full semantic mode

For real semantic retrieval and real answers:

```dotenv
EMBEDDING_BACKEND=sentence-transformers
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
```

The first request that needs embeddings will download the `all-MiniLM-L6-v2` model (a one-time download, cached locally).

---

## 3. Frontend setup

### Windows / macOS / Linux (same commands)

```bash
cd frontend
npm install
npm run dev        # dev server at http://localhost:5173
```

Other useful scripts:

```bash
npm run build      # production build into dist/
npm run test       # vitest unit tests
npm run lint       # ESLint
```

### Pointing the frontend at the backend

The frontend reads the API base URL from `VITE_API_BASE_URL`:

- **Local dev default:** `http://localhost:8000/api`
- **Production default:** `/api`

To override, create `frontend/.env.local`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000/api
# If your backend has API_KEY set, also provide:
VITE_API_KEY=your_shared_api_key
```

> `VITE_API_KEY` is only needed when the backend has `API_KEY` configured (i.e., auth is enabled). In default local dev with no `API_KEY`, leave it unset.

---

## 4. Running both together (two terminals)

| Terminal 1 (backend) | Terminal 2 (frontend) |
| --- | --- |
| `cd backend` | `cd frontend` |
| activate venv | `npm install` (first time) |
| `uvicorn app.main:app --reload --port 8000` | `npm run dev` |

Open `http://localhost:5173`, upload one of the files in `sample-data/`, and ask a question.

---

## 5. Docker Compose (one command)

If you have Docker installed, you can skip the manual setup:

```bash
docker compose up --build        # from the repo root
```

- Backend: `http://localhost:8080`
- Frontend: `http://localhost:5173`

Stop and remove containers:

```bash
docker compose down
```

> Note the backend runs on **:8080** inside Docker (vs. :8000 for the typical local `uvicorn` run). Configure environment via the compose file and your `.env`.

---

## 6. Try it with sample data

The repo ships synthetic documents in `sample-data/`:

- `acme-remote-work-policy.md`
- `acme-security-handbook.txt`
- `acme-pto-benefits.md`
- `evaluation-set.json` (used by the semantic evaluation test — see [TESTING.md](TESTING.md))

Upload one or more and ask questions like _"How many PTO days do employees get?"_ to see grounded answers with citations.

---

## Troubleshooting

### `torch` / sentence-transformers install is huge or slow
`torch` is a large dependency. Options:
- Use **fast mode** (`EMBEDDING_BACKEND=hashing`) for development — no torch needed at runtime for embeddings.
- Ensure you are on a good network; the install and first model download are one-time.

### First request hangs while downloading a model
The first time you use `EMBEDDING_BACKEND=sentence-transformers`, the `all-MiniLM-L6-v2` model downloads and is cached. Subsequent runs are fast. If you want to avoid it entirely, use the hashing backend.

### CORS errors in the browser console
The backend only allows origins listed in `CORS_ALLOW_ORIGINS`. For local dev this includes `http://localhost:5173`. If you changed the frontend port, add that origin to `CORS_ALLOW_ORIGINS` in your backend `.env` and restart.

### `401 / 403` from protected endpoints
If you set `API_KEY` in the backend `.env`, every call to `/api/documents` and `/api/chat` must include the header `X-API-Key: <key>`. Either unset `API_KEY` for local dev, or set `VITE_API_KEY` in the frontend to match.

### Port already in use
- Backend: change `--port 8000` to a free port (and update `VITE_API_BASE_URL`).
- Frontend: run `npm run dev -- --port 5174` and add that origin to `CORS_ALLOW_ORIGINS`.

### `GEMINI_API_KEY` missing → `503`
If `LLM_PROVIDER=gemini` but no valid key is set, chat returns `503`. Either add a key or switch to `LLM_PROVIDER=mock`.

### Health endpoint works but chat fails
Health is always public and does not call the LLM. A failing chat usually points to AI credentials (`503`), timeout (`504`), or quota (`429`). See the error codes in [API.md](API.md).

---

## Next steps

- [CONFIGURATION.md](CONFIGURATION.md) — tune every setting
- [API.md](API.md) — call the API directly with curl
- [TESTING.md](TESTING.md) — run the test suite
- [DEPLOYMENT.md](DEPLOYMENT.md) — ship it to GCP

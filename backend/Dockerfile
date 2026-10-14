# ============================================================================
# Backend container — Enterprise AI Knowledge Assistant (FastAPI)
# ----------------------------------------------------------------------------
# Build context is the `backend/` directory, so paths below are relative to it.
#   docker build -t knowledge-backend ./backend
#
# Design notes:
#  - Single stage keeps things simple. chromadb and PyMuPDF ship prebuilt
#    wheels for linux/amd64, so we normally do NOT need build-essential/gcc.
#    If a future dependency needs to compile, switch to a builder stage that
#    installs `build-essential`, builds wheels, then copies them in.
#  - We run as a non-root user for security (defence in depth).
#  - Cloud Run sends traffic to the port named by $PORT (defaults to 8080).
# ============================================================================
FROM python:3.12-slim

# --- Python runtime behaviour -------------------------------------------------
# PYTHONUNBUFFERED      -> logs stream straight to stdout (good for Cloud Run).
# PYTHONDONTWRITEBYTECODE -> no .pyc files cluttering the image.
# PORT                  -> the port uvicorn listens on (Cloud Run overrides it).
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# --- Create a non-root user up front -----------------------------------------
# uid/gid 1001 is a conventional "first non-system user" id.
RUN groupadd --gid 1001 appuser \
    && useradd --uid 1001 --gid 1001 --no-create-home --shell /usr/sbin/nologin appuser

# --- Install Python dependencies ---------------------------------------------
# Copy ONLY requirements first so Docker can cache this layer and skip the
# (slow) reinstall whenever only application code changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --- Copy the application code ------------------------------------------------
# The `app/` package contains `app.main:app` (the FastAPI instance).
COPY app ./app

# --- Prepare the persistent data directory -----------------------------------
# CHROMA_PERSIST_DIR defaults to ./data/chroma. Create it and hand ownership to
# the non-root user so Chroma can write its SQLite/vector files.
# In Cloud Run this path is backed by a mounted GCS bucket (see Terraform);
# locally it is a bind mount (see docker-compose.yml).
RUN mkdir -p /app/data/chroma \
    && chown -R appuser:appuser /app/data

# Drop privileges.
USER appuser

EXPOSE 8080

# --- Container-level health check --------------------------------------------
# Cloud Run uses its own health probes, but this helps `docker`/compose report
# container health locally. Uses Python's stdlib so we need no extra tools.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://localhost:8080/api/health').status == 200 else sys.exit(1)"

# --- Start the server ---------------------------------------------------------
# Shell form via `sh -c` so ${PORT} is expanded at runtime (Cloud Run injects it).
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]

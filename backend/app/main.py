"""FastAPI application entrypoint.

Wires together configuration, logging, the service container, CORS, security, and
the API routers. Run locally with::

    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api import routes_chat, routes_documents, routes_health
from app.core.config import get_settings
from app.core.container import ServiceContainer
from app.core.logging import configure_logging

API_PREFIX = "/api"
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = app.state.settings
    configure_logging(settings.log_level)
    problems = settings.validate_runtime()
    for p in problems:
        logger.error("CONFIG: %s", p)
    if problems and settings.environment == "production":
        raise RuntimeError("Invalid production configuration: " + "; ".join(problems))
    if not settings.api_key:
        logger.warning(
            "API_KEY is not set — authentication is DISABLED. "
            "Do not run like this outside local development."
        )
    app.state.container = ServiceContainer(settings)
    logger.info(
        "Started %s v%s (env=%s, embeddings=%s, llm=%s)",
        settings.app_name,
        __version__,
        settings.environment,
        app.state.container.embedder.name,
        settings.llm_provider,
    )
    yield
    logger.info("Shutting down.")


def create_app(settings=None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Retrieval-Augmented Generation API for enterprise documents.",
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,  # we use an API-key header, not cookies
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key"],
    )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Never leak internals to clients; log the detail server-side.
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred."},
        )

    @app.get("/", tags=["health"])
    def root():
        return {"status": "ok", "service": settings.app_name, "version": __version__}

    app.include_router(routes_health.router, prefix=API_PREFIX)
    app.include_router(routes_documents.router, prefix=API_PREFIX)
    app.include_router(routes_chat.router, prefix=API_PREFIX)
    return app


app = create_app()

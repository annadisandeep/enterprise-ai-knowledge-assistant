"""Shared FastAPI dependencies for accessing the service container & settings.

Both are read from ``app.state`` (populated at startup) rather than a module-level
singleton, so tests can build an app with bespoke settings without fighting any
cache.
"""

from __future__ import annotations

from fastapi import Request

from app.core.config import Settings
from app.core.container import ServiceContainer


def get_container(request: Request) -> ServiceContainer:
    container = getattr(request.app.state, "container", None)
    if container is None:  # pragma: no cover - only if lifespan didn't run
        raise RuntimeError("Service container is not initialised.")
    return container


def get_settings_dep(request: Request) -> Settings:
    settings = getattr(request.app.state, "settings", None)
    if settings is None:  # pragma: no cover
        raise RuntimeError("Settings are not initialised.")
    return settings

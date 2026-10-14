"""Health and readiness endpoints (unauthenticated)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app import __version__
from app.api.deps import get_container
from app.core.container import ServiceContainer
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(container: ServiceContainer = Depends(get_container)) -> HealthResponse:
    s = container.settings
    return HealthResponse(
        app=s.app_name,
        version=__version__,
        environment=s.environment,
        embedding_backend=container.embedder.name,
        llm_provider=s.llm_provider,
        document_count=container.registry.count(),
    )

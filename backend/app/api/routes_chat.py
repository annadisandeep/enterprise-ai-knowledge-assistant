"""RAG chat endpoint (authenticated)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_container
from app.core.container import ServiceContainer
from app.core.security import require_api_key
from app.models.schemas import ChatRequest, ChatResponse
from app.services.llm_provider import (
    LLMConfigError,
    LLMError,
    LLMQuotaError,
    LLMTimeoutError,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"], dependencies=[Depends(require_api_key)])


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    container: ServiceContainer = Depends(get_container),
) -> ChatResponse:
    try:
        engine = container.get_rag_engine()
        return engine.answer(
            payload.question,
            top_k=payload.top_k,
            document_id=payload.document_id,
        )
    except LLMConfigError as exc:
        # Misconfiguration (e.g. missing key) — a server-side problem.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except LLMTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc)
        ) from exc
    except LLMQuotaError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)
        ) from exc
    except LLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

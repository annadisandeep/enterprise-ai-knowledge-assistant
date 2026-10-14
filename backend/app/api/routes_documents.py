"""Document management endpoints (authenticated)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.api.deps import get_container
from app.core.container import ServiceContainer
from app.core.security import require_api_key
from app.models.schemas import (
    DeleteResponse,
    DocumentListResponse,
    UploadResponse,
)
from app.services.extraction import DocumentError
from app.services.ingestion import DuplicateDocumentError

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(require_api_key)],
)


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    container: ServiceContainer = Depends(get_container),
) -> UploadResponse:
    filename = file.filename or ""
    content = await file.read()
    # Guard against huge uploads before any processing (defence in depth; the
    # reverse proxy / server also limits body size).
    if len(content) > container.settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the maximum allowed size.",
        )
    try:
        meta = container.ingestion.ingest(filename, content)
    except DuplicateDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except DocumentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return UploadResponse(document=meta)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    container: ServiceContainer = Depends(get_container),
) -> DocumentListResponse:
    docs = container.ingestion.list_documents()
    return DocumentListResponse(documents=docs, total=len(docs))


@router.delete("/{document_id}", response_model=DeleteResponse)
def delete_document(
    document_id: str,
    container: ServiceContainer = Depends(get_container),
) -> DeleteResponse:
    existed, chunks = container.ingestion.delete(document_id)
    if not existed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
        )
    return DeleteResponse(id=document_id, deleted_chunks=chunks)

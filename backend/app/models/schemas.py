"""Pydantic request/response models — the public API contract.

These models are the single source of truth shared (conceptually) with the
TypeScript types in ``frontend/src/types``.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str
    version: str
    environment: str
    embedding_backend: str
    llm_provider: str
    document_count: int


class DocumentMetadata(BaseModel):
    """Everything we know about an ingested document."""

    id: str
    filename: str
    content_type: str
    size_bytes: int
    char_count: int
    chunk_count: int
    sha256: str
    uploaded_at: datetime


class UploadResponse(BaseModel):
    document: DocumentMetadata
    message: str = "Document ingested successfully."


class DocumentListResponse(BaseModel):
    documents: list[DocumentMetadata]
    total: int


class DeleteResponse(BaseModel):
    id: str
    deleted_chunks: int
    message: str = "Document deleted."


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    # Optional scoping to a single document; None searches the whole knowledge base.
    document_id: str | None = None


class Citation(BaseModel):
    """A reference to a *real* retrieved passage. Never fabricated."""

    document_id: str
    filename: str
    chunk_id: str
    chunk_index: int
    similarity: float
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    grounded: bool  # True when the answer is backed by retrieved context
    model: str
    used_fallback: bool = False


class ErrorResponse(BaseModel):
    detail: str

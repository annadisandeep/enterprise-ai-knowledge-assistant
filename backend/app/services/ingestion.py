"""Ingestion orchestration: validate -> extract -> chunk -> embed -> store.

This is the single writer that keeps the vector store and the document registry
consistent. It also enforces duplicate detection (by content SHA-256) so the same
file is not indexed twice.
"""

from __future__ import annotations

import hashlib
import logging
import uuid

from app.models.schemas import DocumentMetadata
from app.services.chunking import chunk_text
from app.services.document_registry import DocumentRegistry
from app.services.embeddings import EmbeddingProvider
from app.services.extraction import DocumentError, extract_text, validate_upload
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class DuplicateDocumentError(DocumentError):
    """Raised when an identical document (same SHA-256) already exists."""

    def __init__(self, existing: DocumentMetadata) -> None:
        super().__init__(
            f"This document was already uploaded as '{existing.filename}' "
            f"(id {existing.id})."
        )
        self.existing = existing


_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
}


class IngestionService:
    def __init__(
        self,
        *,
        vector_store: VectorStore,
        registry: DocumentRegistry,
        embedder: EmbeddingProvider,
        allowed_extensions: set[str],
        max_upload_bytes: int,
        chunk_size: int,
        chunk_overlap: int,
    ) -> None:
        self._store = vector_store
        self._registry = registry
        self._embedder = embedder
        self._allowed_extensions = allowed_extensions
        self._max_upload_bytes = max_upload_bytes
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def ingest(self, filename: str, content: bytes) -> DocumentMetadata:
        ext = validate_upload(
            filename,
            content,
            allowed_extensions=self._allowed_extensions,
            max_bytes=self._max_upload_bytes,
        )

        sha256 = hashlib.sha256(content).hexdigest()
        existing = self._registry.find_by_sha256(sha256)
        if existing is not None:
            raise DuplicateDocumentError(existing)

        text = extract_text(filename, content)
        chunks = chunk_text(
            text, chunk_size=self._chunk_size, chunk_overlap=self._chunk_overlap
        )
        if not chunks:
            raise DocumentError("No extractable text found in the document.")

        document_id = uuid.uuid4().hex
        chunk_ids = [f"{document_id}:{c.index}" for c in chunks]
        texts = [c.text for c in chunks]
        embeddings = self._embedder.embed_documents(texts)

        self._store.add_chunks(
            document_id=document_id,
            filename=filename,
            chunk_ids=chunk_ids,
            texts=texts,
            embeddings=embeddings,
        )

        meta = DocumentMetadata(
            id=document_id,
            filename=filename,
            content_type=_CONTENT_TYPES.get(ext, "application/octet-stream"),
            size_bytes=len(content),
            char_count=len(text),
            chunk_count=len(chunks),
            sha256=sha256,
            uploaded_at=DocumentRegistry.now(),
        )
        self._registry.add(meta)
        logger.info("Ingested %s (%d chunks)", filename, len(chunks))
        return meta

    def delete(self, document_id: str) -> tuple[bool, int]:
        """Delete a document and its chunks. Returns (existed, chunk_count)."""
        meta = self._registry.get(document_id)
        if meta is None:
            return False, 0
        self._store.delete_document(document_id)
        self._registry.remove(document_id)
        logger.info("Deleted document %s", document_id)
        return True, meta.chunk_count

    def list_documents(self) -> list[DocumentMetadata]:
        return self._registry.list()

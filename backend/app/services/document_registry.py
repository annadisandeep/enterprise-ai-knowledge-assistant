"""Durable registry of document-level metadata.

Chroma stores per-chunk vectors; this registry stores the per-*document* facts we
need to list the library, show sizes, and detect duplicate uploads (by SHA-256).
It persists to a single JSON file written atomically, and guards access with a
lock so concurrent requests stay consistent. The ingestion service is the only
writer, keeping the registry and the vector store in step.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from datetime import datetime

from app.models.schemas import DocumentMetadata


class DocumentRegistry:
    def __init__(self, path: str) -> None:
        self._path = path
        self._lock = threading.RLock()
        self._docs: dict[str, DocumentMetadata] = {}
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        try:
            with open(self._path, encoding="utf-8") as f:
                raw = json.load(f)
        except (json.JSONDecodeError, OSError):
            raw = {}
        for doc_id, data in raw.items():
            try:
                self._docs[doc_id] = DocumentMetadata(**data)
            except Exception:  # noqa: BLE001 - skip corrupt entries, keep serving
                continue

    def _persist(self) -> None:
        data = {doc_id: json.loads(m.model_dump_json()) for doc_id, m in self._docs.items()}
        directory = os.path.dirname(self._path) or "."
        fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, self._path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def add(self, meta: DocumentMetadata) -> None:
        with self._lock:
            self._docs[meta.id] = meta
            self._persist()

    def remove(self, document_id: str) -> DocumentMetadata | None:
        with self._lock:
            meta = self._docs.pop(document_id, None)
            if meta is not None:
                self._persist()
            return meta

    def get(self, document_id: str) -> DocumentMetadata | None:
        with self._lock:
            return self._docs.get(document_id)

    def find_by_sha256(self, sha256: str) -> DocumentMetadata | None:
        with self._lock:
            for meta in self._docs.values():
                if meta.sha256 == sha256:
                    return meta
            return None

    def list(self) -> list[DocumentMetadata]:
        with self._lock:
            return sorted(self._docs.values(), key=lambda m: m.uploaded_at, reverse=True)

    def count(self) -> int:
        with self._lock:
            return len(self._docs)

    @staticmethod
    def now() -> datetime:
        return datetime.now().astimezone()

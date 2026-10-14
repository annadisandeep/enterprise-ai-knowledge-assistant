"""Chroma-backed vector store for document chunks.

We supply our own embeddings (from :mod:`app.services.embeddings`) rather than
letting Chroma download its default ONNX model, so the collection uses the cosine
space and we stay fully in control of the embedding backend. Similarity is
reported as ``1 - cosine_distance`` (1.0 == identical).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import chromadb
from chromadb.config import Settings as ChromaSettings

# Chroma 0.5.x emits noisy ERROR logs when its optional telemetry backend fails to
# initialise, even with telemetry disabled. Silence it; it is harmless.
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    filename: str
    chunk_index: int
    text: str
    similarity: float


class VectorStore:
    def __init__(self, persist_dir: str, collection_name: str) -> None:
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        *,
        document_id: str,
        filename: str,
        chunk_ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
    ) -> None:
        if not chunk_ids:
            return
        metadatas = [
            {
                "document_id": document_id,
                "filename": filename,
                "chunk_index": i,
            }
            for i in range(len(chunk_ids))
        ]
        self._collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

    def query(
        self,
        query_embedding: list[float],
        *,
        top_k: int,
        document_id: str | None = None,
    ) -> list[RetrievedChunk]:
        where = {"document_id": document_id} if document_id else None
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]
        out: list[RetrievedChunk] = []
        for cid, text, meta, dist in zip(ids, docs, metas, dists, strict=False):
            out.append(
                RetrievedChunk(
                    chunk_id=cid,
                    document_id=str(meta.get("document_id", "")),
                    filename=str(meta.get("filename", "")),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    text=text or "",
                    similarity=round(1.0 - float(dist), 6),
                )
            )
        return out

    def delete_document(self, document_id: str) -> None:
        self._collection.delete(where={"document_id": document_id})

    def count(self) -> int:
        return self._collection.count()

    def reset(self) -> None:
        """Danger: wipe the collection. Used by tests only."""
        ids = self._collection.get().get("ids", [])
        if ids:
            self._collection.delete(ids=ids)

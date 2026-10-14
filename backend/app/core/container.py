"""Dependency container.

Builds and holds the long-lived service singletons for the process. Cheap services
(embedder shell, vector store, registry, ingestion) are created eagerly; the LLM
provider is created lazily on first use so the app can start — and serve document
management and the health check — even when the AI key is absent in local dev.
"""

from __future__ import annotations

import logging

from app.core.config import Settings
from app.services.document_registry import DocumentRegistry
from app.services.embeddings import EmbeddingProvider, build_embedder
from app.services.ingestion import IngestionService
from app.services.llm_provider import GeminiProvider, LLMProvider, MockLLMProvider
from app.services.rag_engine import RAGEngine
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class ServiceContainer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embedder: EmbeddingProvider = build_embedder(
            backend=settings.embedding_backend,
            model_name=settings.embedding_model,
            dimension=settings.embedding_dim,
        )
        self.vector_store = VectorStore(
            persist_dir=settings.chroma_persist_dir,
            collection_name=settings.chroma_collection,
        )
        self.registry = DocumentRegistry(
            path=f"{settings.chroma_persist_dir.rstrip('/')}/documents.json"
        )
        self.ingestion = IngestionService(
            vector_store=self.vector_store,
            registry=self.registry,
            embedder=self.embedder,
            allowed_extensions=settings.allowed_extensions_set,
            max_upload_bytes=settings.max_upload_bytes,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self._llm: LLMProvider | None = None
        self._rag: RAGEngine | None = None

    def _build_llm(self) -> LLMProvider:
        s = self.settings
        if s.llm_provider == "mock":
            return MockLLMProvider(model=s.gemini_model)
        return GeminiProvider(
            api_key=s.gemini_api_key,
            model=s.gemini_model,
            temperature=s.llm_temperature,
            max_output_tokens=s.llm_max_output_tokens,
            timeout_seconds=s.llm_timeout_seconds,
        )

    def get_rag_engine(self) -> RAGEngine:
        """Lazily build the RAG engine (and its LLM provider)."""
        if self._rag is None:
            self._llm = self._build_llm()
            self._rag = RAGEngine(
                vector_store=self.vector_store,
                embedder=self.embedder,
                llm=self._llm,
                top_k=self.settings.retrieval_top_k,
                min_similarity=self.settings.min_similarity,
                max_context_chars=self.settings.max_context_chars,
            )
        return self._rag

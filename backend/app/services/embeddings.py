"""Embedding providers.

Two interchangeable backends behind one interface:

* ``SentenceTransformerEmbedder`` — a real local transformer model
  (``all-MiniLM-L6-v2``, 384-dim) that produces *semantic* embeddings. This is the
  production default: no per-token cost and documents never leave the machine.

* ``HashingEmbedder`` — a deterministic, dependency-light *lexical* embedder
  (a hashing bag-of-words vectoriser). It needs no model download or torch, so it
  is used in CI and unit tests for speed and reproducibility. It captures lexical
  overlap (shared words ⇒ higher cosine) which is enough to exercise retrieval
  logic deterministically, though it is weaker than semantic search for paraphrases.

Both return L2-normalised vectors so that cosine similarity == dot product and the
Chroma cosine space behaves predictably.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol, runtime_checkable

_TOKEN_RE = re.compile(r"[a-z0-9]+")


@runtime_checkable
class EmbeddingProvider(Protocol):
    name: str
    dimension: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


def _l2_normalise(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return vec
    return [v / norm for v in vec]


class HashingEmbedder:
    """Deterministic lexical embeddings via feature hashing. No external deps."""

    def __init__(self, dimension: int = 384) -> None:
        self.name = "hashing"
        self.dimension = dimension

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dimension
        tokens = _TOKEN_RE.findall(text.lower())
        for tok in tokens:
            digest = hashlib.md5(tok.encode("utf-8")).digest()  # noqa: S324 - not security
            bucket = int.from_bytes(digest[:4], "big") % self.dimension
            # Signed hashing reduces collisions cancelling each other out poorly.
            sign = 1.0 if digest[4] & 1 else -1.0
            vec[bucket] += sign
        return _l2_normalise(vec)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text)


class SentenceTransformerEmbedder:
    """Semantic embeddings using a local sentence-transformers model (lazy-loaded)."""

    def __init__(self, model_name: str, dimension: int) -> None:
        self.name = model_name
        self.dimension = dimension
        self._model_name = model_name
        self._model = None  # loaded on first use to keep startup fast

    def _ensure_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
            actual = self._model.get_sentence_embedding_dimension()
            if actual != self.dimension:
                # Trust the model and correct our config-derived value.
                self.dimension = actual
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        model = self._ensure_model()
        vectors = model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True
        )
        return [v.tolist() for v in vectors]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def build_embedder(backend: str, model_name: str, dimension: int) -> EmbeddingProvider:
    """Factory that constructs the configured embedding provider."""
    if backend == "hashing":
        return HashingEmbedder(dimension=dimension)
    if backend == "sentence-transformers":
        return SentenceTransformerEmbedder(model_name=model_name, dimension=dimension)
    raise ValueError(f"Unknown embedding backend: {backend!r}")

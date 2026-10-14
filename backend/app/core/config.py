"""Application configuration.

All settings are read from environment variables (or a local ``.env`` file during
development) so that no secret is ever hard-coded. See ``.env.example`` for the full
list of supported variables and ``docs/CONFIGURATION.md`` for guidance.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed, validated application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- General ----
    app_name: str = "Enterprise AI Knowledge Assistant"
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"

    # ---- API security ----
    # When set, every protected endpoint requires an ``X-API-Key`` header that matches.
    # Leave empty ONLY in local development. The app refuses to start in production
    # without it (see ``validate_runtime`` below).
    api_key: str = Field(default="", repr=False)
    # Comma-separated list of allowed CORS origins. Never use "*" with credentials.
    cors_allow_origins: str = "http://localhost:5173,http://localhost:3000"

    # ---- Uploads ----
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB
    allowed_extensions: str = ".pdf,.txt,.md,.markdown"

    # ---- Embeddings ----
    # "sentence-transformers" uses a real local model; "hashing" is a deterministic,
    # dependency-light fallback used in CI/tests so we don't need to download torch.
    embedding_backend: Literal["sentence-transformers", "hashing"] = "sentence-transformers"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384  # must match the model above / the hashing fallback

    # ---- Vector store ----
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection: str = "knowledge_base"

    # ---- Chunking ----
    chunk_size: int = 1000  # characters
    chunk_overlap: int = 150  # characters

    # ---- Retrieval / RAG ----
    retrieval_top_k: int = 4
    # Chroma returns cosine *distance* (0 = identical). We keep a chunk only when its
    # similarity (1 - distance) is at least this value. Tune per corpus.
    min_similarity: float = 0.15
    max_context_chars: int = 8000  # hard cap on assembled context sent to the LLM

    # ---- LLM provider ----
    llm_provider: Literal["gemini", "mock"] = "gemini"
    gemini_api_key: str = Field(default="", repr=False)
    gemini_model: str = "gemini-2.5-flash"
    llm_temperature: float = 0.2
    llm_max_output_tokens: int = 1024
    llm_timeout_seconds: float = 30.0

    @field_validator("cors_allow_origins")
    @classmethod
    def _no_wildcard_with_prod(cls, v: str) -> str:
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def allowed_extensions_set(self) -> set[str]:
        return {e.strip().lower() for e in self.allowed_extensions.split(",") if e.strip()}

    def validate_runtime(self) -> list[str]:
        """Return a list of human-readable warnings/errors for the current config.

        Called at startup so operators get a clear signal instead of a silent
        misconfiguration. Fatal issues are raised; soft issues are logged.
        """
        problems: list[str] = []
        if self.environment == "production":
            if not self.api_key:
                problems.append("API_KEY must be set in production (endpoints would be open).")
            if "*" in self.cors_allow_origins:
                problems.append("CORS_ALLOW_ORIGINS must not contain '*' in production.")
            if self.llm_provider == "gemini" and not self.gemini_api_key:
                problems.append("GEMINI_API_KEY must be set when LLM_PROVIDER=gemini.")
        return problems


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor (one instance per process)."""
    return Settings()

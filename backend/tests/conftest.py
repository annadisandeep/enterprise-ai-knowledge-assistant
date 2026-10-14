"""Shared pytest fixtures.

Unit and API tests run with the fast, deterministic *hashing* embedder and the
*mock* LLM provider so they need no model download and no network. The semantic
embedder is exercised separately in ``test_eval.py`` (skipped if unavailable).
"""

from __future__ import annotations

import itertools

import pytest
from app.core.config import Settings
from app.core.container import ServiceContainer
from app.main import create_app
from fastapi.testclient import TestClient

_counter = itertools.count()


def make_settings(tmp_path, **overrides) -> Settings:
    base = {
        "environment": "development",
        "api_key": "",
        "cors_allow_origins": "http://localhost:5173",
        "embedding_backend": "hashing",
        "embedding_dim": 256,
        "llm_provider": "mock",
        "chroma_persist_dir": str(tmp_path / f"chroma-{next(_counter)}"),
        "chroma_collection": "test_kb",
        "min_similarity": 0.1,
        "retrieval_top_k": 4,
        "chunk_size": 400,
        "chunk_overlap": 50,
        "max_upload_bytes": 1024 * 1024,
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)


@pytest.fixture
def build_container(tmp_path):
    """Factory for a bare service container (no HTTP layer)."""

    def _build(**overrides) -> ServiceContainer:
        return ServiceContainer(make_settings(tmp_path, **overrides))

    return _build


@pytest.fixture
def make_client(tmp_path):
    """Factory that returns a started TestClient with the given settings overrides."""
    clients: list[TestClient] = []

    def _make(**overrides) -> TestClient:
        settings = make_settings(tmp_path, **overrides)
        app = create_app(settings)
        client = TestClient(app, raise_server_exceptions=False)
        client.__enter__()
        clients.append(client)
        return client

    yield _make
    for c in clients:
        c.__exit__(None, None, None)


@pytest.fixture
def client(make_client) -> TestClient:
    return make_client()

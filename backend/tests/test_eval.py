"""End-to-end RAG evaluation on the synthetic Acme corpus.

This is the one test that uses the *real* semantic sentence-transformers embedder
(to prove genuine semantic retrieval works), while still mocking the LLM. It is
skipped automatically if the model/deps are unavailable or cannot be loaded
(e.g. offline CI without the cached model), so the fast suite never depends on it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.core.config import Settings
from app.core.container import ServiceContainer
from app.services.llm_provider import MockLLMProvider
from app.services.rag_engine import FALLBACK_ANSWER

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DIR = REPO_ROOT / "sample-data"
EVAL_FILE = SAMPLE_DIR / "evaluation-set.json"


def _semantic_available() -> bool:
    try:
        from app.services.embeddings import SentenceTransformerEmbedder

        emb = SentenceTransformerEmbedder(
            "sentence-transformers/all-MiniLM-L6-v2", 384
        )
        emb.embed_query("warm-up")  # forces model load / download
        return True
    except Exception:  # noqa: BLE001 - any failure => skip, don't fail the suite
        return False


pytestmark = pytest.mark.skipif(
    not _semantic_available(),
    reason="sentence-transformers model not available (offline or not installed)",
)


@pytest.fixture(scope="module")
def eval_data():
    return json.loads(EVAL_FILE.read_text(encoding="utf-8"))


@pytest.fixture
def engine_and_state(tmp_path, eval_data):
    settings = Settings(
        _env_file=None,
        embedding_backend="sentence-transformers",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        embedding_dim=384,
        llm_provider="mock",
        chroma_persist_dir=str(tmp_path / "chroma"),
        chroma_collection="eval_kb",
        min_similarity=0.1,
        retrieval_top_k=4,
    )
    container = ServiceContainer(settings)

    # Ingest the sample corpus.
    for name in eval_data["documents"]:
        content = (SAMPLE_DIR / name).read_bytes()
        container.ingestion.ingest(name, content)

    # A mock LLM standing in for a well-behaved grounded model. The `answerable`
    # flag is toggled per case to emulate the model finding (or not finding) the
    # answer in the retrieved context. This keeps the LLM mocked while the test
    # still verifies *real* semantic retrieval via the returned citations.
    state = {"answerable": True}

    def handler(system, prompt):
        if state["answerable"]:
            return "According to the documents, here is the grounded answer. [Source 1]"
        return FALLBACK_ANSWER

    container._build_llm = lambda: MockLLMProvider(handler=handler)
    return container.get_rag_engine(), state, eval_data


def test_grounded_cases_retrieve_correct_source(engine_and_state):
    engine, state, data = engine_and_state
    for case in data["cases"]:
        if case["type"] != "grounded":
            continue
        state["answerable"] = True
        resp = engine.answer(case["question"])
        assert resp.grounded is True, f"{case['id']} should be grounded"
        assert resp.citations, f"{case['id']} should have citations"
        # Real semantic retrieval must surface the correct source document.
        top_sources = {c.filename for c in resp.citations}
        assert case["expected_source"] in top_sources, (
            f"{case['id']}: expected {case['expected_source']} in {top_sources}"
        )


def test_no_answer_cases_trigger_fallback(engine_and_state):
    engine, state, data = engine_and_state
    for case in data["cases"]:
        if case["type"] != "no_answer":
            continue
        state["answerable"] = False
        resp = engine.answer(case["question"])
        assert resp.used_fallback is True, f"{case['id']} should fall back"
        assert resp.grounded is False

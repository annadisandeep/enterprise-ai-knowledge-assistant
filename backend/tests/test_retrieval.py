from app.services.embeddings import HashingEmbedder
from app.services.vector_store import VectorStore


def _store(tmp_path):
    return VectorStore(persist_dir=str(tmp_path / "chroma"), collection_name="testcol")


def _add(store, emb, doc_id, filename, texts):
    store.add_chunks(
        document_id=doc_id,
        filename=filename,
        chunk_ids=[f"{doc_id}:{i}" for i in range(len(texts))],
        texts=texts,
        embeddings=emb.embed_documents(texts),
    )


def test_semantic_search_returns_most_relevant_first(tmp_path):
    store = _store(tmp_path)
    emb = HashingEmbedder(dimension=512)
    _add(
        store,
        emb,
        "d1",
        "facts.txt",
        [
            "The capital of France is Paris.",
            "The Eiffel Tower is a famous landmark.",
            "Photosynthesis converts sunlight into chemical energy.",
        ],
    )
    results = store.query(emb.embed_query("What is the capital of France?"), top_k=3)
    assert results
    assert "capital of France is Paris" in results[0].text
    # similarity is in [0, 1] and sorted descending
    sims = [r.similarity for r in results]
    assert sims == sorted(sims, reverse=True)


def test_configurable_top_k_limits_results(tmp_path):
    store = _store(tmp_path)
    emb = HashingEmbedder(dimension=256)
    _add(store, emb, "d1", "f.txt", [f"chunk about topic {i}" for i in range(10)])
    assert len(store.query(emb.embed_query("topic"), top_k=3)) == 3


def test_document_filter_scopes_search(tmp_path):
    store = _store(tmp_path)
    emb = HashingEmbedder(dimension=256)
    _add(store, emb, "d1", "a.txt", ["alpha content about budgets"])
    _add(store, emb, "d2", "b.txt", ["alpha content about budgets"])
    results = store.query(emb.embed_query("budgets"), top_k=5, document_id="d2")
    assert results
    assert all(r.document_id == "d2" for r in results)


def test_delete_document_removes_its_chunks(tmp_path):
    store = _store(tmp_path)
    emb = HashingEmbedder(dimension=256)
    _add(store, emb, "d1", "a.txt", ["keep me around"])
    _add(store, emb, "d2", "b.txt", ["delete me soon"])
    assert store.count() == 2
    store.delete_document("d2")
    assert store.count() == 1
    results = store.query(emb.embed_query("delete me"), top_k=5)
    assert all(r.document_id != "d2" for r in results)

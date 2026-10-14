import math

from app.services.embeddings import HashingEmbedder, build_embedder


def _cosine(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def test_hashing_embedder_dimension_and_normalisation():
    emb = HashingEmbedder(dimension=128)
    vec = emb.embed_query("the capital of france is paris")
    assert len(vec) == 128
    assert math.isclose(math.sqrt(sum(v * v for v in vec)), 1.0, rel_tol=1e-6)


def test_hashing_embedder_is_deterministic():
    emb = HashingEmbedder(dimension=128)
    a = emb.embed_query("hello world")
    b = emb.embed_query("hello world")
    assert a == b


def test_lexical_similarity_orders_related_above_unrelated():
    emb = HashingEmbedder(dimension=512)
    query = emb.embed_query("how many vacation days do employees accrue")
    related = emb.embed_documents(["Employees accrue vacation days each year."])[0]
    unrelated = emb.embed_documents(["The server rack temperature is 21 degrees."])[0]
    assert _cosine(query, related) > _cosine(query, unrelated)


def test_build_embedder_factory_hashing():
    emb = build_embedder("hashing", "unused", 256)
    assert emb.name == "hashing"
    assert emb.dimension == 256


def test_empty_text_embeds_to_zero_vector():
    emb = HashingEmbedder(dimension=64)
    vec = emb.embed_query("")
    assert all(v == 0.0 for v in vec)

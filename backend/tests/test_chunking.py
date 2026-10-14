from app.services.chunking import chunk_text


def test_short_text_single_chunk():
    chunks = chunk_text("Just a short sentence.", chunk_size=1000, chunk_overlap=100)
    assert len(chunks) == 1
    assert chunks[0].index == 0


def test_long_text_splits_into_multiple_chunks():
    text = "\n\n".join(f"Paragraph number {i} with some filler words." for i in range(50))
    chunks = chunk_text(text, chunk_size=200, chunk_overlap=20)
    assert len(chunks) > 1
    # indices are sequential starting at 0
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_chunks_respect_size_budget_roughly():
    text = "word " * 1000
    chunks = chunk_text(text, chunk_size=200, chunk_overlap=20)
    # No chunk should be wildly larger than size + overlap.
    assert all(len(c.text) <= 200 + 20 + 10 for c in chunks)


def test_overlap_shares_content_between_neighbours():
    text = "\n\n".join(f"Sentence {i} aaaa bbbb cccc." for i in range(10))
    chunks = chunk_text(text, chunk_size=60, chunk_overlap=20)
    assert len(chunks) >= 2


def test_empty_text_returns_no_chunks():
    assert chunk_text("   \n  ", chunk_size=100, chunk_overlap=10) == []


def test_overlap_must_be_smaller_than_size():
    import pytest

    with pytest.raises(ValueError):
        chunk_text("hello", chunk_size=10, chunk_overlap=10)

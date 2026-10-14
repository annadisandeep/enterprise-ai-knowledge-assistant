import pytest
from app.services.extraction import DocumentError, extract_text, validate_upload

from tests.fixtures import make_pdf_bytes

ALLOWED = {".pdf", ".txt", ".md", ".markdown"}
MAX = 1024 * 1024


# ---- validate_upload ----
def test_rejects_unsupported_extension():
    with pytest.raises(DocumentError, match="Unsupported"):
        validate_upload("malware.exe", b"data", allowed_extensions=ALLOWED, max_bytes=MAX)


def test_rejects_empty_file():
    with pytest.raises(DocumentError, match="empty"):
        validate_upload("a.txt", b"", allowed_extensions=ALLOWED, max_bytes=MAX)


def test_rejects_oversized_file():
    with pytest.raises(DocumentError, match="too large"):
        validate_upload("a.txt", b"x" * (MAX + 1), allowed_extensions=ALLOWED, max_bytes=MAX)


def test_rejects_pdf_with_bad_signature():
    with pytest.raises(DocumentError, match="signature"):
        validate_upload("a.pdf", b"not really a pdf", allowed_extensions=ALLOWED, max_bytes=MAX)


def test_accepts_valid_txt():
    ext = validate_upload("notes.TXT", b"hello", allowed_extensions=ALLOWED, max_bytes=MAX)
    assert ext == ".txt"


# ---- extract_text ----
def test_extract_txt():
    text = extract_text("a.txt", b"Hello world\nSecond line")
    assert "Hello world" in text
    assert "Second line" in text


def test_extract_markdown():
    text = extract_text("a.md", b"# Title\n\nBody text here.")
    assert "Title" in text and "Body text here." in text


def test_extract_rejects_binary_text():
    with pytest.raises(DocumentError, match="binary"):
        extract_text("a.txt", b"abc\x00\x01def")


def test_extract_rejects_whitespace_only():
    with pytest.raises(DocumentError, match="No extractable text"):
        extract_text("a.txt", b"   \n\n   ")


def test_extract_pdf_roundtrip():
    pdf = make_pdf_bytes("The quick brown fox jumps over the lazy dog.")
    text = extract_text("doc.pdf", pdf)
    assert "quick brown fox" in text

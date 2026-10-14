"""Helpers to build binary fixtures (PDFs) on the fly for tests."""

from __future__ import annotations


def make_pdf_bytes(text: str) -> bytes:
    """Create a minimal single-page PDF containing ``text`` using PyMuPDF."""
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=12)
    data = doc.tobytes()
    doc.close()
    return data

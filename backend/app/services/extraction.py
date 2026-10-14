"""Document validation and text extraction.

Supported types: PDF (via PyMuPDF), plain text, and Markdown. We validate the
declared extension, the real file signature where one exists, the size, and that
the extracted text is non-empty. All failures raise :class:`DocumentError` with a
safe, user-facing message.
"""

from __future__ import annotations

import os

import fitz  # PyMuPDF


class DocumentError(ValueError):
    """Raised for any invalid/unsupported/empty document. Message is user-safe."""


# Minimal magic-byte signatures. Text formats have no reliable signature, so we
# instead verify they decode as text and are not predominantly binary.
_PDF_MAGIC = b"%PDF-"


def _ext(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def validate_upload(
    filename: str,
    content: bytes,
    *,
    allowed_extensions: set[str],
    max_bytes: int,
) -> str:
    """Validate an uploaded file. Returns the normalised extension on success."""
    if not filename:
        raise DocumentError("A filename is required.")
    ext = _ext(filename)
    if ext not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise DocumentError(f"Unsupported file type '{ext or '(none)'}'. Allowed: {allowed}.")
    size = len(content)
    if size == 0:
        raise DocumentError("The uploaded file is empty.")
    if size > max_bytes:
        raise DocumentError(
            f"File is too large ({size} bytes). Maximum allowed is {max_bytes} bytes."
        )
    if ext == ".pdf" and not content.startswith(_PDF_MAGIC):
        raise DocumentError("File does not appear to be a valid PDF (bad signature).")
    return ext


def _extract_pdf(content: bytes) -> str:
    try:
        with fitz.open(stream=content, filetype="pdf") as doc:
            if doc.is_encrypted and not doc.authenticate(""):
                raise DocumentError("Encrypted PDFs are not supported.")
            parts = [page.get_text("text") for page in doc]
    except DocumentError:
        raise
    except Exception as exc:  # noqa: BLE001 - PyMuPDF raises broad exceptions
        raise DocumentError("Could not read the PDF file; it may be corrupt.") from exc
    return "\n".join(parts)


def _extract_text(content: bytes) -> str:
    # A text/markdown file should decode cleanly. A NUL byte is a strong binary signal.
    if b"\x00" in content:
        raise DocumentError("File looks binary, not text.")
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise DocumentError("Could not decode the text file (unknown encoding).")


def extract_text(filename: str, content: bytes) -> str:
    """Extract and normalise text from a validated upload.

    Assumes :func:`validate_upload` already ran. Raises :class:`DocumentError`
    when no usable text can be extracted.
    """
    ext = _ext(filename)
    # PDF needs binary parsing; everything else (.txt/.md/.markdown) decodes as text.
    text = _extract_pdf(content) if ext == ".pdf" else _extract_text(content)
    text = _normalise(text)
    if not text.strip():
        raise DocumentError("No extractable text found in the document.")
    return text


def _normalise(text: str) -> str:
    # Normalise line endings and collapse runs of blank lines / trailing spaces.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in text.split("\n")]
    out: list[str] = []
    blank = 0
    for ln in lines:
        if ln == "":
            blank += 1
            if blank <= 2:
                out.append(ln)
        else:
            blank = 0
            out.append(ln)
    return "\n".join(out).strip()

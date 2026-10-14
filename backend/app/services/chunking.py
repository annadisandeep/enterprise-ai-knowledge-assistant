"""Text chunking.

A recursive, boundary-aware character splitter. We try to break on the largest
natural separator that fits (paragraphs, then lines, then sentences, then words)
so chunks stay semantically coherent, with a configurable character overlap so a
fact that straddles a boundary is still retrievable from at least one chunk.
"""

from __future__ import annotations

from dataclasses import dataclass

_SEPARATORS = ["\n\n", "\n", ". ", " "]


@dataclass(frozen=True)
class Chunk:
    index: int
    text: str


def _split_recursive(text: str, chunk_size: int, separators: list[str]) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    if not separators:
        # No separator left: hard-split oversized token.
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    sep, *rest = separators
    pieces = text.split(sep)
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        candidate = piece if not current else current + sep + piece
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(piece) > chunk_size:
            chunks.extend(_split_recursive(piece, chunk_size, rest))
            current = ""
        else:
            current = piece
    if current.strip():
        chunks.append(current)
    return chunks


def _apply_overlap(chunks: list[str], overlap: int) -> list[str]:
    if overlap <= 0 or len(chunks) < 2:
        return chunks
    out = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tail = chunks[i - 1][-overlap:]
        out.append((prev_tail + " " + chunks[i]).strip())
    return out


def chunk_text(text: str, *, chunk_size: int = 1000, chunk_overlap: int = 150) -> list[Chunk]:
    """Split ``text`` into overlapping, boundary-aware chunks."""
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
    text = text.strip()
    if not text:
        return []
    raw = _split_recursive(text, chunk_size, _SEPARATORS)
    raw = [c.strip() for c in raw if c.strip()]
    overlapped = _apply_overlap(raw, chunk_overlap)
    return [Chunk(index=i, text=c) for i, c in enumerate(overlapped)]

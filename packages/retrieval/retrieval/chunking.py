"""Fixed-overlap token-window text chunker."""
from __future__ import annotations


def chunk_text(
    text: str,
    chunk_size: int = 200,
    chunk_overlap: int = 50,
) -> list[str]:
    """Split *text* into overlapping windows of approximately *chunk_size* words.

    Uses word-boundary splitting as a proxy for token splitting (avoids a
    hard dependency on a tokenizer in this layer). The caller is responsible
    for token-counting if strict token budgets are required.

    All original content appears in at least one chunk, and adjacent chunks
    share *chunk_overlap* words at their boundary.
    """
    if not text:
        return []

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        step = chunk_size - chunk_overlap
        if step <= 0:
            break
        start += step

    return chunks


def chunk_documents(
    documents: list[dict],
    text_key: str = "content",
    chunk_size: int = 200,
    chunk_overlap: int = 50,
) -> list[dict]:
    """Chunk a list of document dicts, preserving metadata.

    Each returned dict contains all original keys plus:
    - ``chunk_index``: 0-based index within the source document
    - ``chunk_text``: the chunk content (original *text_key* is replaced)
    """
    result: list[dict] = []
    for doc in documents:
        text = doc.get(text_key, "")
        chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        for i, chunk in enumerate(chunks):
            entry = {k: v for k, v in doc.items() if k != text_key}
            entry[text_key] = chunk
            entry["chunk_index"] = i
            result.append(entry)
    return result

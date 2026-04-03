"""retrieval — public interface for hybrid search and document chunking."""
from __future__ import annotations

import logging

from .chunking import chunk_documents, chunk_text
from .service import DocumentChunk, RetrievalService

logger = logging.getLogger(__name__)

__all__ = [
    "RetrievalService",
    "DocumentChunk",
    "chunk_text",
    "chunk_documents",
]

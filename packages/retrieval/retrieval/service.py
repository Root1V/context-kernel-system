"""RetrievalService — the single entry point for all external context retrieval."""
from __future__ import annotations

from typing import Any

from .chunking import chunk_documents
from .filters import apply_filters
from .hybrid_search import HybridSearcher
from .rerank import Reranker


class DocumentChunk:
    """Normalized retrieval result returned to callers."""

    def __init__(
        self,
        id: str,
        content: str,
        source_type: str,
        score: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.id = id
        self.content = content
        self.source_type = source_type
        self.score = score
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"DocumentChunk(id={self.id!r}, score={self.score:.3f})"


class RetrievalService:
    """Hybrid BM25 + vector retrieval with reranking and metadata filtering.

    *corpus* is a list of document dicts with at least ``id``, ``content``,
    and ``source_type`` keys, plus optionally an ``embedding`` float list.
    In production this is loaded from the DB / pgvector on startup.
    """

    def __init__(
        self,
        corpus: list[dict[str, Any]] | None = None,
        reranker_model: str | None = None,
    ) -> None:
        self._corpus: list[dict[str, Any]] = corpus or []
        self._reranker = Reranker(model_name=reranker_model)

    def load_corpus(self, corpus: list[dict[str, Any]]) -> None:
        self._corpus = corpus

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
        query_embedding: list[float] | None = None,
    ) -> list[DocumentChunk]:
        """Execute hybrid search with optional pre-filtering and reranking.

        This is the ONLY function in the system allowed to perform retrieval.
        All packages must go through this method — never query the DB directly.
        """
        # 1. Pre-filter by metadata
        candidates = apply_filters(self._corpus, filters or {})

        # 2. Hybrid BM25 + vector search
        searcher = HybridSearcher(candidates)
        raw_results = searcher.search(query, query_embedding, top_k=top_k * 2)

        # 3. Rerank top candidates
        reranked = self._reranker.rerank(query, raw_results, top_k=top_k)

        # 4. Normalize to DocumentChunk
        return [
            DocumentChunk(
                id=str(r.get("id", "")),
                content=r.get("content", ""),
                source_type=r.get("source_type", "unknown"),
                score=r.get("_rerank_score", r.get("_score", 0.0)),
                metadata={k: v for k, v in r.items() if not k.startswith("_")},
            )
            for r in reranked
        ]

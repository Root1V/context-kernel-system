"""RetrievalService — the single entry point for all external context retrieval."""

from __future__ import annotations

from typing import Any, Optional

from .filters import apply_filters
from .hybrid_search import HybridSearcher
from .rerank import Reranker


def _archival_entry_to_corpus_dict(row: Any) -> dict[str, Any]:
    """Convert an ArchivalEntry ORM row to the corpus dict format for HybridSearcher."""
    meta: dict[str, Any] = row.metadata_ or {}
    return {
        "id": str(row.id),
        "content": row.content,
        "source_type": meta.get("source_type", "archival"),
        "embedding": list(row.embedding) if row.embedding is not None else [],
        **{k: v for k, v in meta.items() if k != "source_type"},
    }


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

    *session_factory* is an optional async SQLAlchemy session factory. When set,
    ``async_search`` queries ``ArchivalRepository`` and loads the corpus from the DB.
    """

    def __init__(
        self,
        corpus: list[dict[str, Any]] | None = None,
        reranker_model: str | None = None,
        session_factory: Optional[Any] = None,
    ) -> None:
        self._corpus: list[dict[str, Any]] = corpus or []
        self._reranker = Reranker(model_name=reranker_model)
        self._session_factory = session_factory

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

    async def async_search(
        self,
        session_id: str,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """DB-backed search: loads corpus from ArchivalRepository then runs hybrid scoring.

        Falls back to the in-memory ``search()`` when ``session_factory`` is None.
        """
        if self._session_factory is None:
            return self.search(query, top_k=top_k, filters=filters)

        import uuid as _uuid

        from storage.repositories.memory_blocks import ArchivalRepository

        async with self._session_factory() as db:
            repo = ArchivalRepository(db)
            sid: Any
            try:
                sid = _uuid.UUID(session_id) if isinstance(session_id, str) else session_id
            except ValueError:
                sid = session_id  # not a UUID string; pass as-is to the repository
            rows = await repo.search(sid, embedding=[], top_k=top_k * 2)

        corpus = [_archival_entry_to_corpus_dict(row) for row in rows]
        if not corpus:
            return []

        # Run hybrid BM25 + vector scoring over the loaded corpus
        candidates = apply_filters(corpus, filters or {})
        searcher = HybridSearcher(candidates)
        raw_results = searcher.search(query, None, top_k=top_k * 2)
        reranked = self._reranker.rerank(query, raw_results, top_k=top_k)

        return [
            DocumentChunk(
                id=str(r.get("id", "")),
                content=r.get("content", ""),
                source_type=r.get("source_type", "archival"),
                score=r.get("_rerank_score", r.get("_score", 0.0)),
                metadata={k: v for k, v in r.items() if not k.startswith("_")},
            )
            for r in reranked
        ]

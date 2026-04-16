"""Unit tests for retrieval-pipeline — covers all spec scenarios."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from retrieval import DocumentChunk, RetrievalService, chunk_text
from retrieval.filters import apply_filters
from retrieval.hybrid_search import HybridSearcher
from retrieval.rerank import Reranker

CORPUS = [
    {
        "id": "1",
        "content": "Python async patterns and coroutines",
        "source_type": "codebase",
        "embedding": [1.0, 0.0, 0.0],
    },
    {
        "id": "2",
        "content": "SQL joins and database normalization",
        "source_type": "docs",
        "embedding": [0.0, 1.0, 0.0],
    },
    {
        "id": "3",
        "content": "Python decorators and metaclasses",
        "source_type": "codebase",
        "embedding": [0.9, 0.1, 0.0],
    },
]


class TestChunking:
    def test_all_content_covered(self):
        text = " ".join(f"word{i}" for i in range(100))
        chunks = chunk_text(text, chunk_size=20, chunk_overlap=5)
        reconstructed = set()
        for chunk in chunks:
            reconstructed.update(chunk.split())
        original_words = set(text.split())
        assert reconstructed == original_words

    def test_adjacent_chunks_share_overlap(self):
        text = " ".join(str(i) for i in range(20))
        chunks = chunk_text(text, chunk_size=10, chunk_overlap=3)
        if len(chunks) >= 2:
            last_words = set(chunks[0].split()[-3:])
            first_words = set(chunks[1].split()[:3])
            assert len(last_words & first_words) > 0

    def test_empty_text_returns_empty(self):
        assert chunk_text("") == []


class TestFilters:
    def test_source_type_filter(self):
        result = apply_filters(CORPUS, {"source_type": "codebase"})
        assert all(d["source_type"] == "codebase" for d in result)
        assert len(result) == 2

    def test_no_filter_returns_all(self):
        result = apply_filters(CORPUS, {})
        assert len(result) == len(CORPUS)

    def test_non_matching_filter_returns_empty(self):
        result = apply_filters(CORPUS, {"source_type": "nonexistent"})
        assert result == []


class TestHybridSearch:
    def test_returns_top_k_results(self):
        searcher = HybridSearcher(CORPUS)
        results = searcher.search("Python async", query_embedding=None, top_k=2)
        assert len(results) == 2

    def test_results_are_deduplicated(self):
        # Duplicate corpus shouldn't produce duplicate IDs
        dup_corpus = CORPUS + [CORPUS[0].copy()]
        searcher = HybridSearcher(dup_corpus)
        results = searcher.search("Python", query_embedding=None, top_k=5)
        ids = [r["id"] for r in results]
        assert len(ids) == len(set(ids))

    def test_vector_boosts_semantic_match(self):
        searcher = HybridSearcher(CORPUS)
        # Query embedding closest to doc 2 (SQL)
        results = searcher.search("databases", query_embedding=[0.0, 1.0, 0.0], top_k=3)
        assert results[0]["id"] == "2"


class TestReranker:
    def test_reranker_reorders_by_relevance(self):
        candidates = [
            {"id": "b", "content": "SQL joins thoroughly explained"},
            {"id": "a", "content": "Python async coding patterns"},
        ]
        reranker = Reranker()
        result = reranker.rerank("python async", candidates, top_k=2)
        assert result[0]["id"] == "a"

    def test_empty_candidates_returns_empty(self):
        reranker = Reranker()
        assert reranker.rerank("query", []) == []


class TestRetrievalService:
    def test_search_returns_document_chunks(self):
        svc = RetrievalService(corpus=CORPUS)
        results = svc.search("Python async", top_k=3)
        assert all(isinstance(r, DocumentChunk) for r in results)
        assert len(results) <= 3

    def test_filter_restricts_results(self):
        svc = RetrievalService(corpus=CORPUS)
        results = svc.search("Python", top_k=10, filters={"source_type": "docs"})
        assert all(r.source_type == "docs" for r in results)

    def test_orchestrator_uses_service_not_db(self):
        """Ensures external callers only see the service interface."""
        svc = RetrievalService(corpus=CORPUS)
        assert hasattr(svc, "search")
        # The service must not expose raw DB methods
        assert not hasattr(svc, "execute")
        assert not hasattr(svc, "query")


class TestAsyncRetrievalService:
    @pytest.mark.asyncio
    async def test_async_search_no_factory_returns_empty(self):
        """Without a session_factory, async_search falls back to in-memory search (empty corpus)."""
        svc = RetrievalService()  # no corpus, no session_factory
        result = await svc.async_search("sess-1", "python async")
        assert result == []

    @pytest.mark.asyncio
    async def test_async_search_no_factory_uses_loaded_corpus(self):
        """When session_factory is None, async_search returns from in-memory corpus."""
        svc = RetrievalService(corpus=CORPUS)
        result = await svc.async_search("sess-1", "python async", top_k=2)
        assert all(isinstance(r, DocumentChunk) for r in result)
        assert len(result) <= 2

    @pytest.mark.asyncio
    async def test_async_search_with_mock_factory(self):
        """async_search queries ArchivalRepository and converts rows to DocumentChunks."""
        mock_row = MagicMock()
        mock_row.id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        mock_row.content = "Python async patterns"
        mock_row.embedding = None
        mock_row.metadata_ = {"source_type": "codebase"}

        mock_repo = AsyncMock()
        mock_repo.search.return_value = [mock_row]

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        def factory():
            return mock_session

        mock_module = MagicMock()
        mock_module.ArchivalRepository = MagicMock(return_value=mock_repo)
        with patch.dict(
            "sys.modules",
            {
                "storage.repositories.memory_blocks": mock_module,
            },
        ):
            svc = RetrievalService(session_factory=factory)
            results = await svc.async_search(
                "00000000-0000-0000-0000-000000000099", "python async", top_k=5
            )

        assert len(results) == 1
        assert results[0].content == "Python async patterns"
        assert isinstance(results[0], DocumentChunk)

    @pytest.mark.asyncio
    async def test_async_search_empty_db_returns_empty(self):
        """When DB returns no rows, async_search returns []."""
        mock_repo = AsyncMock()
        mock_repo.search.return_value = []

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        def factory():
            return mock_session

        mock_module = MagicMock()
        mock_module.ArchivalRepository = MagicMock(return_value=mock_repo)
        with patch.dict(
            "sys.modules",
            {
                "storage.repositories.memory_blocks": mock_module,
            },
        ):
            svc = RetrievalService(session_factory=factory)
            results = await svc.async_search(
                "00000000-0000-0000-0000-000000000099", "any query", top_k=5
            )

        assert results == []

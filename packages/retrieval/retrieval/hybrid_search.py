"""Hybrid BM25 + vector search with score fusion and deduplication."""
from __future__ import annotations

import math
from typing import Any


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    ma = math.sqrt(sum(x * x for x in a))
    mb = math.sqrt(sum(x * x for x in b))
    if ma == 0 or mb == 0:
        return 0.0
    return dot / (ma * mb)


def _bm25_score(
    query_terms: list[str],
    doc_terms: list[str],
    doc_lengths: list[int],
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Simplified BM25 score for a single document."""
    avg_len = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1
    dl = len(doc_terms)
    score = 0.0
    term_freq = {}
    for t in doc_terms:
        term_freq[t] = term_freq.get(t, 0) + 1

    for term in set(query_terms):
        tf = term_freq.get(term, 0)
        if tf == 0:
            continue
        idf = math.log(1 + 1)  # simplified: treat every term as present in 1 doc
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * dl / avg_len)
        score += idf * numerator / denominator
    return score


class HybridSearcher:
    """BM25 + vector similarity hybrid search over in-memory document corpus.

    In production the vector branch is replaced by the pgvector repository;
    injection is done via *vector_search_fn*.
    """

    def __init__(
        self,
        corpus: list[dict[str, Any]],
        text_key: str = "content",
        id_key: str = "id",
        vector_key: str = "embedding",
        vector_search_fn=None,
    ) -> None:
        self._corpus = corpus
        self._text_key = text_key
        self._id_key = id_key
        self._vector_key = vector_key
        self._vector_search_fn = vector_search_fn
        self._doc_lengths = [len(d.get(text_key, "").split()) for d in corpus]

    def search(
        self, query: str, query_embedding: list[float] | None, top_k: int = 10
    ) -> list[dict[str, Any]]:
        """Return top_k results ranked by fused BM25 + cosine score."""
        query_terms = query.lower().split()
        scores: dict[str, float] = {}

        for i, doc in enumerate(self._corpus):
            doc_terms = doc.get(self._text_key, "").lower().split()
            bm25 = _bm25_score(query_terms, doc_terms, self._doc_lengths)
            vector_score = 0.0
            if query_embedding and doc.get(self._vector_key):
                vector_score = _cosine_similarity(query_embedding, doc[self._vector_key])
            # Reciprocal rank fusion style: simple weighted sum
            fused = 0.5 * bm25 + 0.5 * vector_score
            doc_id = str(doc.get(self._id_key, i))
            scores[doc_id] = max(scores.get(doc_id, 0), fused)

        # Build deduplicated ranked list
        ranked_ids = sorted(scores, key=lambda k: scores[k], reverse=True)[:top_k]
        id_to_doc = {str(d.get(self._id_key, i)): d for i, d in enumerate(self._corpus)}
        return [{**id_to_doc[did], "_score": scores[did]} for did in ranked_ids if did in id_to_doc]

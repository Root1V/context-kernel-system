"""Cross-encoder reranker applied to top-N retrieval candidates.

In production, uses a sentence-transformer cross-encoder model.
Falls back to BM25-style keyword overlap scoring when the model is unavailable.
"""

from __future__ import annotations

from typing import Any


def _keyword_overlap_score(query: str, text: str) -> float:
    q_terms = set(query.lower().split())
    t_terms = set(text.lower().split())
    if not q_terms:
        return 0.0
    return len(q_terms & t_terms) / len(q_terms)


class Reranker:
    """Re-orders candidates by relevance to the query.

    If *model_name* is provided, attempts to load a cross-encoder via
    sentence-transformers. Falls back to keyword overlap if unavailable.
    """

    def __init__(self, model_name: str | None = None, text_key: str = "content") -> None:
        self._model_name = model_name
        self._text_key = text_key
        self._model = None
        if model_name:
            try:
                from sentence_transformers import CrossEncoder

                self._model = CrossEncoder(model_name)
            except ImportError:
                pass  # Fallback to keyword scoring

    def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """Return candidates re-ordered by cross-encoder relevance score."""
        if not candidates:
            return []

        if self._model is not None:
            pairs = [(query, c.get(self._text_key, "")) for c in candidates]
            scores = self._model.predict(pairs)
            ranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
            result = [{**c, "_rerank_score": float(s)} for s, c in ranked]
        else:
            result = sorted(
                [
                    {**c, "_rerank_score": _keyword_overlap_score(query, c.get(self._text_key, ""))}
                    for c in candidates
                ],
                key=lambda x: x["_rerank_score"],
                reverse=True,
            )

        return result[:top_k] if top_k else result

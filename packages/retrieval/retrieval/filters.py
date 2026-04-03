"""Metadata pre-filtering for candidate documents before BM25/vector search."""

from __future__ import annotations

from typing import Any


def apply_filters(docs: list[dict], filters: dict[str, Any]) -> list[dict]:
    """Return only documents matching ALL key=value pairs in *filters*.

    Supports top-level string equality. Nested keys (using dot notation)
    are resolved recursively.
    """
    if not filters:
        return docs

    result = []
    for doc in docs:
        if _matches(doc, filters):
            result.append(doc)
    return result


def _matches(doc: dict, filters: dict[str, Any]) -> bool:
    for key, expected in filters.items():
        if "." in key:
            parts = key.split(".", 1)
            nested = doc.get(parts[0], {})
            if not isinstance(nested, dict) or not _matches(nested, {parts[1]: expected}):
                return False
        else:
            if doc.get(key) != expected:
                return False
    return True

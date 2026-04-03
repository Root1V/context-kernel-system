"""TokenBudget — model-aware token counting wrapper for the Context Assembler.

Delegates all counting and limit lookups to `model_adapter` so that token
limits are never hard-coded here.
"""

from __future__ import annotations

import os
import sys

# Allow importing model_adapter from the monorepo packages directory.
_PACKAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
if _PACKAGES_DIR not in sys.path:
    sys.path.insert(0, _PACKAGES_DIR)


class TokenBudget:
    """Stateless token budget helper bound to a specific model."""

    def __init__(self, model_id: str) -> None:
        self._model_id = model_id
        try:
            from model_adapter import count_tokens as _count
            from model_adapter import get_context_limit as _limit

            self._count = _count
            self._limit_fn = _limit
        except ImportError:
            # Fallback: rough char/4 heuristic (no tokenizer available)
            self._count = lambda text, model: max(1, len(text) // 4)  # type: ignore[assignment]
            self._limit_fn = lambda model: 8192  # type: ignore[assignment]

    def count(self, text: str) -> int:
        """Return the token count for *text* under this budget's model."""
        return self._count(text, self._model_id)

    def context_limit(self) -> int:
        """Return the model's total context-window size (in tokens)."""
        return self._limit_fn(self._model_id)

    def available(self, response_reserve: int = 1024) -> int:
        """Total tokens available for the prompt (context limit minus response reserve)."""
        return max(0, self.context_limit() - response_reserve)

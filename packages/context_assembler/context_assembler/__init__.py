"""context_assembler — exclusive composer of prompt payloads.

All other packages MUST import exclusively from this module.
"""

from __future__ import annotations

import logging

from .assembler import (
    ActiveContext,
    AssemblyInput,
    ContextAssembler,
    PromptSection,
    SectionPriority,
)
from .token_budget import TokenBudget

logger = logging.getLogger(__name__)

__all__ = [
    "ContextAssembler",
    "ActiveContext",
    "AssemblyInput",
    "PromptSection",
    "SectionPriority",
    "TokenBudget",
]

# Convenience singleton — callers may use this or instantiate their own.
_assembler = ContextAssembler()


def assemble(inp: AssemblyInput) -> ActiveContext:
    """Assemble an `ActiveContext` for a single turn.

    This is a module-level convenience wrapper around `ContextAssembler.assemble()`.
    It is stateless: each call is fully independent.
    """
    logger.debug("assemble.start", extra={"model_id": inp.model_id})
    result = _assembler.assemble(inp)
    logger.debug("assemble.end", extra={"tokens_used": result.total_tokens})
    return result

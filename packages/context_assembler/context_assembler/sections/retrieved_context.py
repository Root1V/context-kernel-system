"""Section builder — retrieved document chunks (non-pinned, lowest priority)."""
from __future__ import annotations

from ..assembler import PromptSection, SectionPriority
from ..token_budget import TokenBudget


def build_section(chunks: list[str], budget: TokenBudget) -> PromptSection:
    content = "\n\n".join(f"<chunk>\n{c}\n</chunk>" for c in chunks)
    return PromptSection(
        name="retrieved_chunks",
        priority=SectionPriority.RETRIEVED_CHUNKS,
        content=content,
        pinned=False,
        token_count=budget.count(content),
    )

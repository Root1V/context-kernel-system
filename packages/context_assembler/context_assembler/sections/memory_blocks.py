"""Section builder — core memory blocks (pinned)."""

from __future__ import annotations

from ..assembler import PromptSection, SectionPriority
from ..token_budget import TokenBudget


def build_section(core_memory_blocks: list[str], budget: TokenBudget) -> PromptSection:
    content = "\n".join(f"[CORE_MEMORY] {block}" for block in core_memory_blocks)
    return PromptSection(
        name="core_memory",
        priority=SectionPriority.CORE_MEMORY,
        content=content,
        pinned=True,
        token_count=budget.count(content),
    )

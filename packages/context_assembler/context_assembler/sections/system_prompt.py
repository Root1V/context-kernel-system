"""Section builder — system instructions (pinned, top priority)."""

from __future__ import annotations

from ..assembler import PromptSection, SectionPriority
from ..token_budget import TokenBudget


def build_section(system_instructions: str, budget: TokenBudget) -> PromptSection:
    content = system_instructions.strip()
    return PromptSection(
        name="system_instructions",
        priority=SectionPriority.SYSTEM_INSTRUCTIONS,
        content=content,
        pinned=True,
        token_count=budget.count(content),
    )

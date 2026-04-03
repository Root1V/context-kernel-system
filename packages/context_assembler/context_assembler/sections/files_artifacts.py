"""Section builder — open files / workspace artifacts."""
from __future__ import annotations

from ..assembler import PromptSection, SectionPriority
from ..token_budget import TokenBudget


def build_section(open_files: list[str], budget: TokenBudget) -> PromptSection:
    content = "\n\n".join(f"<file>\n{f}\n</file>" for f in open_files)
    return PromptSection(
        name="open_files",
        priority=SectionPriority.OPEN_FILES,
        content=content,
        pinned=False,
        token_count=budget.count(content),
    )

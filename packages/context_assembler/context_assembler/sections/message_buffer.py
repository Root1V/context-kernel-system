"""Section builder — recent message buffer (non-pinned, second-lowest priority)."""

from __future__ import annotations

from ..assembler import PromptSection, SectionPriority
from ..token_budget import TokenBudget


def build_section(messages: list[str], budget: TokenBudget) -> PromptSection:
    content = "\n".join(messages)
    return PromptSection(
        name="message_buffer",
        priority=SectionPriority.MESSAGE_BUFFER,
        content=content,
        pinned=False,
        token_count=budget.count(content),
    )

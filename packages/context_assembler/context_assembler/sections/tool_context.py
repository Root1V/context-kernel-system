"""Section builder — tool schemas."""
from __future__ import annotations

import json
from typing import Any

from ..assembler import PromptSection, SectionPriority
from ..token_budget import TokenBudget


def build_section(tool_schemas: list[dict[str, Any]], budget: TokenBudget) -> PromptSection:
    content = json.dumps(tool_schemas, separators=(",", ":"), sort_keys=True)
    return PromptSection(
        name="tool_schemas",
        priority=SectionPriority.TOOL_SCHEMAS,
        content=content,
        pinned=False,
        token_count=budget.count(content),
    )

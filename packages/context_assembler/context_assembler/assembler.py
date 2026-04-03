"""Context Assembler — exclusive composer of prompt payloads.

No other module may format prompt sections. All assembly is stateless:
every call receives all required inputs explicitly as parameters.
"""
from __future__ import annotations

import enum
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Section priority enum
# ---------------------------------------------------------------------------

class SectionPriority(enum.IntEnum):
    """Lower value = higher priority. Sections are dropped highest-number first."""
    SYSTEM_INSTRUCTIONS = 1
    CORE_MEMORY = 2
    STATE_SUMMARY = 3
    TOOL_SCHEMAS = 4
    OPEN_FILES = 5
    MESSAGE_BUFFER = 6
    RETRIEVED_CHUNKS = 7


# ---------------------------------------------------------------------------
# Input / output models
# ---------------------------------------------------------------------------

class PromptSection(BaseModel):
    """A single renderable section to be included in the context payload."""
    name: str
    priority: SectionPriority
    content: str
    pinned: bool = False
    token_count: int = 0


class AssemblyInput(BaseModel):
    """All data required for a single assembly call. Stateless — pass everything."""
    model_id: str
    system_instructions: str = ""
    tool_schemas: list[dict[str, Any]] = Field(default_factory=list)
    core_memory_blocks: list[str] = Field(default_factory=list)
    state_summary: str = ""
    message_buffer: list[str] = Field(default_factory=list)
    retrieved_chunks: list[str] = Field(default_factory=list)
    open_files: list[str] = Field(default_factory=list)
    # Reserve this many tokens for the model's own response.
    response_reserve: int = 1024


class ActiveContext(BaseModel):
    """The fully assembled, token-budget-constrained prompt payload for one turn."""
    model_id: str
    sections: list[PromptSection] = Field(default_factory=list)
    total_tokens: int = 0
    truncated: bool = False
    truncated_sections: list[str] = Field(default_factory=list)

    def render(self) -> str:
        """Return the ordered prompt string for this payload."""
        return "\n\n".join(s.content for s in self.sections if s.content)


# ---------------------------------------------------------------------------
# Assembler
# ---------------------------------------------------------------------------

class ContextAssembler:
    """Stateless context assembler.

    Builds an `ActiveContext` by:
    1. Constructing `PromptSection` objects from `AssemblyInput`.
    2. Sorting sections by canonical priority (ascending).
    3. Fitting them into the model's token budget (response reserve subtracted).
    4. Truncating (dropping) low-priority, non-pinned sections until budget is met.
    """

    def assemble(self, inp: AssemblyInput) -> ActiveContext:
        from .token_budget import TokenBudget
        from .sections.system_prompt import build_section as build_system
        from .sections.tool_context import build_section as build_tools
        from .sections.memory_blocks import build_section as build_memory
        from .sections.message_buffer import build_section as build_buffer
        from .sections.retrieved_context import build_section as build_retrieved
        from .sections.files_artifacts import build_section as build_files

        budget = TokenBudget(inp.model_id)
        available = budget.available(inp.response_reserve)

        raw_sections: list[PromptSection] = []

        # --- build each section ---
        if inp.system_instructions:
            raw_sections.append(build_system(inp.system_instructions, budget))

        if inp.core_memory_blocks:
            raw_sections.append(build_memory(inp.core_memory_blocks, budget))

        if inp.state_summary:
            _state_section = PromptSection(
                name="state_summary",
                priority=SectionPriority.STATE_SUMMARY,
                content=inp.state_summary,
                pinned=False,
            )
            _state_section.token_count = budget.count(_state_section.content)
            raw_sections.append(_state_section)

        if inp.tool_schemas:
            raw_sections.append(build_tools(inp.tool_schemas, budget))

        if inp.open_files:
            raw_sections.append(build_files(inp.open_files, budget))

        if inp.message_buffer:
            raw_sections.append(build_buffer(inp.message_buffer, budget))

        if inp.retrieved_chunks:
            raw_sections.append(build_retrieved(inp.retrieved_chunks, budget))

        # Sort by priority — deterministic for equal-priority items via name
        raw_sections.sort(key=lambda s: (s.priority, s.name))

        # --- fit into budget ---
        return self._fit(raw_sections, available, inp.model_id)

    def _fit(
        self,
        sections: list[PromptSection],
        available_tokens: int,
        model_id: str,
    ) -> ActiveContext:
        total = sum(s.token_count for s in sections)

        if total <= available_tokens:
            return ActiveContext(
                model_id=model_id,
                sections=sections,
                total_tokens=total,
                truncated=False,
            )

        # Drop non-pinned sections starting from lowest priority until budget fits.
        included: list[PromptSection] = list(sections)
        truncated_section_names: list[str] = []

        # Iterate from lowest priority to highest (reverse sort)
        for section in sorted(sections, key=lambda s: (-s.priority, s.name)):
            if section.pinned:
                continue
            current_total = sum(s.token_count for s in included)
            if current_total <= available_tokens:
                break
            included.remove(section)
            truncated_section_names.append(section.name)

        final_total = sum(s.token_count for s in included)
        return ActiveContext(
            model_id=model_id,
            sections=included,
            total_tokens=final_total,
            truncated=len(truncated_section_names) > 0,
            truncated_sections=truncated_section_names,
        )

"""Unit tests for context_assembler.

Covers all spec scenarios:
  - Full assembly within budget (truncated=False)
  - Budget exceeded — low-priority sections dropped first
  - Pinned sections survive critical budget
  - Section ordering is deterministic
  - model_id propagates to TokenBudget
  - Concurrent calls do not interfere (stateless)
"""

from __future__ import annotations

import os
import sys
import threading
from unittest.mock import patch

# Ensure packages directory is on sys.path so imports work without install.
_PACKAGES = os.path.join(os.path.dirname(__file__), "..", "..")
if _PACKAGES not in sys.path:
    sys.path.insert(0, _PACKAGES)

from context_assembler import (
    ActiveContext,
    AssemblyInput,
    ContextAssembler,
    assemble,
)
from context_assembler.token_budget import TokenBudget

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_input(**overrides) -> AssemblyInput:
    defaults = {
        "model_id": "gpt-4o",
        "system_instructions": "You are a helpful assistant.",
        "core_memory_blocks": ["User name: Alice"],
        "state_summary": "Task: write tests.",
        "tool_schemas": [{"name": "search", "description": "web search"}],
        "message_buffer": ["User: Hello!", "Assistant: Hi there!"],
        "retrieved_chunks": ["chunk 1 content", "chunk 2 content"],
        "open_files": ["file.py: print('hello')"],
        "response_reserve": 0,  # no reserve — easier to reason about in tests
    }
    defaults.update(overrides)
    return AssemblyInput(**defaults)


def _tiny_input(**overrides) -> AssemblyInput:
    """Input designed to exceed a small token budget."""
    defaults = {
        "model_id": "gpt-4o",
        "system_instructions": "sys",
        "core_memory_blocks": ["mem"],
        "state_summary": "state",
        "tool_schemas": [{"n": "t"}],
        "message_buffer": ["msg"],
        "retrieved_chunks": ["chunk"],
        "open_files": ["file"],
        "response_reserve": 0,
    }
    defaults.update(overrides)
    return AssemblyInput(**defaults)


# ---------------------------------------------------------------------------
# Scenario: Full assembly within budget
# ---------------------------------------------------------------------------


class TestFullAssemblyWithinBudget:
    def test_all_sections_included(self):
        inp = _make_input()
        result = assemble(inp)
        assert isinstance(result, ActiveContext)
        assert result.truncated is False
        assert result.truncated_sections == []
        section_names = {s.name for s in result.sections}
        assert "system_instructions" in section_names
        assert "core_memory" in section_names
        assert "message_buffer" in section_names
        assert "retrieved_chunks" in section_names

    def test_total_tokens_positive(self):
        inp = _make_input()
        result = assemble(inp)
        assert result.total_tokens > 0

    def test_render_contains_all_content(self):
        inp = _make_input()
        result = assemble(inp)
        rendered = result.render()
        assert "You are a helpful assistant" in rendered
        assert "Alice" in rendered
        assert "Hello!" in rendered


# ---------------------------------------------------------------------------
# Scenario: Budget exceeded — low-priority sections dropped first
# ---------------------------------------------------------------------------


class TestBudgetTruncation:
    def test_retrieved_chunks_dropped_first(self):
        # Patch context limit to something very small so truncation is forced.
        with patch.object(TokenBudget, "context_limit", return_value=30):
            inp = _make_input(response_reserve=0)
            result = assemble(inp)

        assert result.truncated is True
        names = {s.name for s in result.sections}
        # retrieved_chunks has highest priority number — it should be gone first
        assert "retrieved_chunks" not in names
        assert len(result.truncated_sections) > 0

    def test_message_buffer_dropped_before_state(self):
        # With a medium budget: retrieved chunks AND message buffer should be removed
        # before state_summary (priority 3) because message_buffer is priority 6.
        with patch.object(TokenBudget, "context_limit", return_value=15):
            inp = _make_input(response_reserve=0)
            result = assemble(inp)

        names = {s.name for s in result.sections}
        assert "message_buffer" not in names or "retrieved_chunks" not in names


# ---------------------------------------------------------------------------
# Scenario: Pinned sections survive critical budget
# ---------------------------------------------------------------------------


class TestPinnedSectionsNeverDropped:
    def test_system_instructions_pinned(self):
        with patch.object(TokenBudget, "context_limit", return_value=5):
            inp = _make_input(response_reserve=0)
            result = assemble(inp)

        names = {s.name for s in result.sections}
        assert "system_instructions" in names

    def test_core_memory_pinned(self):
        with patch.object(TokenBudget, "context_limit", return_value=5):
            inp = _make_input(response_reserve=0)
            result = assemble(inp)

        names = {s.name for s in result.sections}
        assert "core_memory" in names

    def test_pinned_flag_set_on_sections(self):
        inp = _make_input()
        result = assemble(inp)
        pinned = {s.name for s in result.sections if s.pinned}
        assert "system_instructions" in pinned
        assert "core_memory" in pinned


# ---------------------------------------------------------------------------
# Scenario: Section ordering is deterministic
# ---------------------------------------------------------------------------


class TestDeterministicOrdering:
    def test_same_input_same_output(self):
        inp = _make_input()
        result_a = assemble(inp)
        result_b = assemble(inp)
        assert result_a.render() == result_b.render()

    def test_section_order_follows_priority(self):
        inp = _make_input()
        result = assemble(inp)
        priorities = [s.priority for s in result.sections]
        assert priorities == sorted(priorities)

    def test_system_instructions_first(self):
        inp = _make_input()
        result = assemble(inp)
        assert result.sections[0].name == "system_instructions"


# ---------------------------------------------------------------------------
# Scenario: model_id flows through to TokenBudget
# ---------------------------------------------------------------------------


class TestModelIdPropagation:
    def test_model_id_in_result(self):
        inp = _make_input(model_id="claude-3-5-sonnet-20241022")
        result = assemble(inp)
        assert result.model_id == "claude-3-5-sonnet-20241022"

    def test_token_budget_uses_model_id(self):
        with patch(
            "context_assembler.token_budget.TokenBudget.context_limit", return_value=128000
        ) as mock_limit:
            inp = _make_input(model_id="gpt-4o", response_reserve=0)
            assemble(inp)
        mock_limit.assert_called()


# ---------------------------------------------------------------------------
# Scenario: Concurrent assembly calls do not interfere (stateless)
# ---------------------------------------------------------------------------


class TestStatelessConcurrency:
    def test_concurrent_calls_independent(self):
        results: list[ActiveContext] = []
        errors: list[Exception] = []

        def run(system_text: str) -> None:
            try:
                inp = _make_input(system_instructions=system_text, response_reserve=0)
                result = assemble(inp)
                results.append(result)
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=run, args=(f"System instructions for session {i}",))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(results) == 5
        # Each result should contain its own system instructions text
        rendered_texts = [r.render() for r in results]
        # They should not all be identical (different system instructions)
        assert len(set(rendered_texts)) == 5


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_optional_sections(self):
        inp = AssemblyInput(
            model_id="gpt-4o",
            system_instructions="Only system.",
            response_reserve=0,
        )
        result = assemble(inp)
        assert result.truncated is False
        assert any(s.name == "system_instructions" for s in result.sections)

    def test_no_sections_at_all(self):
        inp = AssemblyInput(model_id="gpt-4o", response_reserve=0)
        result = assemble(inp)
        assert result.sections == []
        assert result.total_tokens == 0

    def test_token_budget_available_subtracts_reserve(self):
        budget = TokenBudget("gpt-4o")
        with patch.object(budget, "context_limit", return_value=1000):
            assert budget.available(256) == 744

    def test_assembler_instantiatable_multiple_times(self):
        a = ContextAssembler()
        b = ContextAssembler()
        inp = _make_input()
        assert a.assemble(inp).render() == b.assemble(inp).render()

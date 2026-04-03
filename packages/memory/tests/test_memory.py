"""Unit tests for layered-memory — covers all spec scenarios."""
from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from memory import (
    ArchivalEntry,
    CoreMemoryBlock,
    MemoryService,
    MessageTurn,
    RecallEntry,
    RecallEntryType,
)


@pytest.fixture
def svc() -> MemoryService:
    return MemoryService(max_core_tokens=100, recall_window_hours=1.0, message_buffer_size=3)


class TestCoreMemory:
    def test_block_stored_and_retrieved(self, svc):
        sid = uuid4()
        block = CoreMemoryBlock(session_id=sid, label="user", content="Alice", token_count=10)
        svc.add_core_memory_block(block)
        blocks = svc.get_core_memory(sid)
        assert any(b.label == "user" for b in blocks)

    def test_budget_evicts_lowest_scored_block(self, svc):
        sid = uuid4()
        # max_core_tokens=100, add two blocks that together exceed budget
        important = CoreMemoryBlock(session_id=sid, label="important", content="critical", token_count=60, importance_score=0.9)
        trivial = CoreMemoryBlock(session_id=sid, label="trivial", content="meh", token_count=60, importance_score=0.1)
        svc.add_core_memory_block(important)
        svc.add_core_memory_block(trivial)  # triggers eviction of 'important' which was added first
        blocks = svc.get_core_memory(sid)
        # trivial should be evicted (lower score), important should survive
        labels = [b.label for b in blocks]
        assert "important" in labels
        assert "trivial" not in labels

    def test_returns_typed_objects(self, svc):
        sid = uuid4()
        svc.add_core_memory_block(CoreMemoryBlock(session_id=sid, label="l", content="c", token_count=5))
        for b in svc.get_core_memory(sid):
            assert isinstance(b, CoreMemoryBlock)


class TestMessageBuffer:
    def test_buffer_overflow_drops_oldest(self, svc):
        sid = uuid4()
        evicted = []
        svc._on_overflow = evicted.append
        svc._buffers = {}  # reset buffers so on_overflow is applied

        # Rebuild service with overflow handler
        svc2 = MemoryService(message_buffer_size=2, on_buffer_overflow=evicted.append)
        for i in range(3):
            svc2.append_message(sid, MessageTurn(role="user", content=f"msg{i}"))

        msgs = svc2.get_message_buffer(sid)
        assert len(msgs) == 2
        assert len(evicted) == 1
        assert evicted[0].content == "msg0"

    def test_layers_are_independent(self, svc):
        sid = uuid4()
        svc.append_message(sid, MessageTurn(role="user", content="hello"))
        # Reading archival should not trigger any message buffer change
        archival = svc.search_archival(sid, [0.1] * 3, top_k=5)
        assert archival == []
        assert len(svc.get_message_buffer(sid)) == 1


class TestRecallMemory:
    def test_recent_entries_returned(self, svc):
        sid = uuid4()
        entry = RecallEntry(session_id=sid, entry_type=RecallEntryType.tool_call, content="called read_file")
        svc.add_recall_entry(entry)
        entries = svc.get_recall_entries(sid)
        assert any(e.id == entry.id for e in entries)

    def test_expired_entries_not_returned_by_default(self):
        from memory.recall_memory import RecallMemoryService

        svc = RecallMemoryService(recall_window_hours=1.0)
        sid = uuid4()
        old_entry = RecallEntry(
            session_id=sid,
            entry_type=RecallEntryType.decision,
            content="old decision",
            created_at=datetime.utcnow() - timedelta(hours=2),
        )
        svc.add_entry(old_entry)
        active = svc.get_entries(sid)
        assert len(active) == 0
        expired = svc.get_expired_entries(sid)
        assert len(expired) == 1


class TestArchivalMemory:
    def test_search_returns_ranked_results(self, svc):
        sid = uuid4()
        target = ArchivalEntry(session_id=sid, content="Python async patterns", embedding_model="test", embedding=[1.0, 0.0])
        noise = ArchivalEntry(session_id=sid, content="SQL joins", embedding_model="test", embedding=[0.0, 1.0])
        svc.add_archival_entry(target)
        svc.add_archival_entry(noise)

        results = svc.search_archival(sid, query_embedding=[1.0, 0.0], top_k=2)
        assert len(results) == 2
        assert results[0].id == target.id  # most similar first

    def test_search_empty_returns_empty(self, svc):
        sid = uuid4()
        assert svc.search_archival(sid, [0.5, 0.5], top_k=5) == []

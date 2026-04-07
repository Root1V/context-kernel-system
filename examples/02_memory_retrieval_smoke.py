# Run: uv run python3 examples/02_memory_retrieval_smoke.py
"""
Layer 2 — Memory + Retrieval
Packages: memory, retrieval, storage

What this tests:
  - storage DB (PostgreSQL) — creates tables, seeds rows, reads them back
  - memory.MemoryService.snapshot()  →  populated from DB rows
  - retrieval.RetrievalService.search()  →  corpus loaded from document_chunks table

Requires DATABASE_URL in .env (start DB: docker compose -f packages/storage/docker-compose.yml up -d)
"""

import asyncio
import os
import sys
import uuid

from dotenv import load_dotenv

load_dotenv()  # loads .env from the project root

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _pkg in ["memory", "retrieval", "storage"]:  # retrieval depends on storage models
    _d = os.path.join(_ROOT, "packages", _pkg)
    if _d not in sys.path:
        sys.path.insert(0, _d)

SESSION_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
SEARCH_QUERY = "context engineering memory system"

# ---------------------------------------------------------------------------
# All DB work runs inside an async function (SQLAlchemy async engine)
# ---------------------------------------------------------------------------
async def main() -> None:
    from sqlalchemy import select, text

    from storage import Base, init_db
    from storage.db import get_engine, get_session
    from storage.models import (
        CoreMemoryBlock as CoreMemoryRow,
        RecallEntry as RecallEntryRow,
        Session as SessionRow,
    )
    from storage.repositories.documents import DocumentChunkRow, DocumentRepository

    # --- connect & create tables ---
    init_db()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  ✓ Tables ensured via create_all()")

    async with get_session() as db:
        # --- upsert demo session row (needed by FK on core_memory_blocks) ---
        existing = await db.get(SessionRow, SESSION_ID)
        if not existing:
            db.add(SessionRow(id=SESSION_ID))
            await db.flush()

        # --- delete previous demo rows so re-runs don't duplicate ---
        await db.execute(
            text("DELETE FROM core_memory_blocks WHERE session_id = :sid"),
            {"sid": str(SESSION_ID)},
        )
        await db.execute(
            text("DELETE FROM recall_entries WHERE session_id = :sid"),
            {"sid": str(SESSION_ID)},
        )
        await db.execute(
            text("DELETE FROM document_chunks WHERE source_id = 'demo-02'"),
        )

        # --- seed core memory blocks ---
        db.add(CoreMemoryRow(
            session_id=SESSION_ID,
            label="user_identity",
            content="User: Emerce — prefers concise answers and practical examples.",
            token_count=15,
            importance_score=1.0,
        ))
        db.add(CoreMemoryRow(
            session_id=SESSION_ID,
            label="current_project",
            content="Project: context-kernel-system — multi-layer AI agent memory architecture.",
            token_count=14,
            importance_score=0.9,
        ))

        # --- seed recall entries ---
        db.add(RecallEntryRow(
            session_id=SESSION_ID,
            entry_type="decision",
            content="User requested concise explanations during onboarding.",
        ))
        db.add(RecallEntryRow(
            session_id=SESSION_ID,
            entry_type="event",
            content="Session started — project context-kernel-system loaded.",
        ))

        # --- seed document chunks (for retrieval) ---
        doc_corpus = [
            ("Recall memory stores recent conversation facts for fast retrieval within the active session window.", "documentation"),
            ("ContextAssembler respects token budgets and drops lower-priority sections first when context is tight.", "documentation"),
            ("Core memory blocks are always included in every prompt — they represent persistent user context.", "documentation"),
            ("Archival memory uses pgvector embeddings for long-term semantic search across past conversations.", "documentation"),
            ("The orchestrator DAG runs: load_state → hydrate_memory → retrieve_context → assemble_context → infer.", "documentation"),
        ]
        for content, source_type in doc_corpus:
            db.add(DocumentChunkRow(
                source_id="demo-02",
                source_type=source_type,
                content=content,
                token_count=len(content.split()),
            ))

        await db.flush()

    # --- read back from DB ---
    print("\n--- Memory Snapshot (from DB) ---")
    async with get_session() as db:
        core_rows = (await db.execute(
            select(CoreMemoryRow)
            .where(CoreMemoryRow.session_id == SESSION_ID)
            .order_by(CoreMemoryRow.importance_score.desc())
        )).scalars().all()

        recall_rows = (await db.execute(
            select(RecallEntryRow)
            .where(RecallEntryRow.session_id == SESSION_ID)
            .order_by(RecallEntryRow.created_at.desc())
        )).scalars().all()

        print(f"  core_memory    : {len(core_rows)} block(s) from DB")
        for b in core_rows:
            print(f"    [{b.label}] {b.content[:80]}")

        print(f"  recall_entries : {len(recall_rows)} entry(ies) from DB")
        for e in recall_rows:
            print(f"    • [{e.entry_type}] {e.content[:80]}")

        print(f"\n  ✓ Memory data read from PostgreSQL")

    # --- retrieval: load corpus from DB, run hybrid search ---
    print("\n--- Retrieved Chunks (from DB) ---")
    async with get_session() as db:
        chunk_rows = (await db.execute(
            select(DocumentChunkRow).where(DocumentChunkRow.source_id == "demo-02")
        )).scalars().all()

        corpus = [
            {"id": str(r.id), "content": r.content, "source_type": r.source_type}
            for r in chunk_rows
        ]

    from retrieval import RetrievalService

    svc = RetrievalService(corpus=corpus)
    chunks = svc.search(SEARCH_QUERY, top_k=3)

    print(f"  query  : \"{SEARCH_QUERY}\"")
    print(f"  corpus : {len(corpus)} chunk(s) loaded from DB")
    print(f"  found  : {len(chunks)} chunk(s)")

    for i, chunk in enumerate(chunks, 1):
        print(f"\n  Chunk {i} (score={chunk.score:.3f}):")
        print(f"    {chunk.content[:120]}")

    print(f"\n  ✓ RetrievalService returned {len(chunks)} chunk(s) from DB corpus")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
try:
    asyncio.run(main())
except Exception as exc:
    msg = str(exc)
    if "DATABASE_URL" in msg or "connection" in msg.lower():
        print(f"  ⚠️  DB not available: {msg}")
        print("  →  Start the DB: docker compose -f packages/storage/docker-compose.yml up -d")
    else:
        print(f"  ⚠️  fallback: {exc}")

print()

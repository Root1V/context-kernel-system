# Run: uv run python3 examples/01_storage_state_smoke.py
"""
Layer 1 — Storage + State
Packages: storage, state

What this tests:
  - storage.Base.metadata.tables  →  lists all mapped ORM table names (no DB needed)
  - storage.init_db()             →  initialises the SQLAlchemy engine (needs DATABASE_URL)
  - state.StateService            →  reads/writes session state (in-memory fallback, no DB needed)
"""

import os
import sys
import uuid

from dotenv import load_dotenv

load_dotenv()  # loads .env from the project root

# Add each package directory to sys.path so imports resolve correctly.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _pkg in ["storage", "state"]:
    _d = os.path.join(_ROOT, "packages", _pkg)
    if _d not in sys.path:
        sys.path.insert(0, _d)

SESSION_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")  # stable demo UUID

# ---------------------------------------------------------------------------
# Section 1: storage — ORM table registry (no DB connection required)
# ---------------------------------------------------------------------------
print("\n--- Storage Tables ---")
try:
    from storage import Base  # importing storage registers all ORM models

    table_names = list(Base.metadata.tables.keys())
    for name in table_names:
        print(f"  • {name}")
    print(f"\n  ✓ {len(table_names)} ORM tables registered (models loaded, no DB connection needed)")
except Exception as exc:
    print(f"  ⚠️  fallback: {exc}")

# ---------------------------------------------------------------------------
# Section 2: storage — init_db (needs DATABASE_URL env var)
# ---------------------------------------------------------------------------
print("\n--- Storage init_db ---")
try:
    from storage import init_db

    init_db()
    print("  ✓ init_db() succeeded — engine connected to database")
except RuntimeError as exc:
    print(f"  ⚠️  fallback: {exc}")
    print("  →  Start the DB:  docker compose -f packages/storage/docker-compose.yml up -d")
    print("  →  Then run:      DATABASE_URL=postgresql+asyncpg://kernel:kernel@localhost:5433/context_kernel uv run python3 examples/01_storage_state_smoke.py")
except Exception as exc:
    print(f"  ⚠️  fallback: {exc}")

# ---------------------------------------------------------------------------
# Section 3: state — StateService (in-memory, always works)
# ---------------------------------------------------------------------------
print("\n--- Session State ---")
try:
    from state import StateService

    svc = StateService()  # in-memory backend — no DB needed
    session = svc.get_session_state(SESSION_ID)
    print(f"  session_id : {session.session_id}")
    print(f"  created_at : {session.created_at}")
    print(f"  updated_at : {session.updated_at}")
    print(f"\n  ✓ StateService returned SessionState (in-memory backend, no DB needed)")
except Exception as exc:
    print(f"  ⚠️  fallback: {exc}")

print()

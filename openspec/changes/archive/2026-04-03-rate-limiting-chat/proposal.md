# Proposal — rate-limiting-chat

## What

Add per-IP rate limiting to the `POST /chat` endpoint in `apps/api`. Requests that exceed the configured limit receive an HTTP `429 Too Many Requests` response with a `Retry-After` header.

## Why

The `/chat` endpoint invokes the full orchestration DAG (memory, retrieval, LLM call). Without a rate limit, a single client can exhaust compute and external API quota. This is a standard API safety boundary.

## Scope

| In scope | Out of scope |
|---|---|
| Rate limiting `POST /chat` | Rate limiting `/sessions` or `/health` |
| Per-IP limiting (default) | Per-user or per-session-id limiting |
| In-memory store (local dev) | Distributed Redis-backed store |
| Configurable limit via env var | Admin UI or dynamic limit adjustment |
| 429 response + `Retry-After` header | Custom error body schema changes |
| Tests for the rate limit behavior | Load / stress testing |

## Acceptance Criteria

1. `POST /chat` returns `429` when a single IP exceeds the configured limit within the time window.
2. The `429` response includes a `Retry-After` header indicating when the client may retry.
3. The rate limit is configurable via the `CHAT_RATE_LIMIT` environment variable (default: `60/minute`).
4. Requests within the limit continue to return `200` as before.
5. All existing tests continue to pass.
6. A new test suite covers the rate-limited path.

## Constraints

- Must use `slowapi` (the standard FastAPI rate limiting library based on `limits`).
- `uv` is the only allowed dependency manager.
- Python 3.9 compatibility required.
- No changes to `ChatRequest` or `ChatResponse` schemas.
- The quality gate (`bash .git/hooks/pre-push`) must pass after implementation.

# ADR-005: Rate Limiting on the Chat Endpoint

- **Status**: Accepted
- **Date**: 2026-04-03
- **Impacts**: `apps/api`

## Context

The `POST /chat` endpoint invokes the full orchestration DAG — memory retrieval, context assembly, and an LLM call. Without a rate limit, a single client can exhaust compute resources and external API quota (OpenAI, Anthropic). A per-IP rate limit is a standard API safety boundary for any public or semi-public endpoint.

## Decision

Use **`slowapi`** (built on the `limits` library) as the rate limiting layer for the FastAPI application.

- Rate limiting is applied only to `POST /chat`. Other endpoints (`/sessions`, `/health`) are not limited.
- The key function is `get_remote_address` — per-IP limiting using `X-Forwarded-For` or `request.client.host`.
- The rate limit is configurable via the `CHAT_RATE_LIMIT` environment variable (default: `60/minute`).
- In-memory storage is used by default (sufficient for single-instance local/dev deployments).
- Requests exceeding the limit receive `HTTP 429 Too Many Requests` with a `Retry-After` header.
- The limiter is instantiated in a dedicated `apps/api/app/limiter.py` module to avoid circular imports between `main.py` and route handlers.

## Consequences

- **Positive**: Protects compute and external API quota from a single misbehaving or abusive client.
- **Positive**: Configurable without code changes — operators set `CHAT_RATE_LIMIT` per environment.
- **Limitation**: In-memory storage is not shared across multiple API instances. A Redis-backed store (`slowapi` supports this via `limits`) would be required for a horizontally scaled deployment — out of scope for now.
- **Limitation**: Per-IP limiting can be bypassed behind a shared NAT or proxy. Per-user limiting (keyed by session or auth token) is a future extension.

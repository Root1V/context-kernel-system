# Context Kernel API

FastAPI application that exposes the context kernel runtime over HTTP.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/chat` | Submit a user message; runs the full orchestration DAG and returns the assistant response. Rate limited. |
| `POST` | `/sessions` | Create a new session. |
| `GET` | `/sessions/{id}` | Retrieve a session by ID. |
| `GET` | `/health` | Health check. |

## Rate Limiting

`POST /chat` is rate-limited per client IP using [`slowapi`](https://github.com/laurentS/slowapi).

| Config | Default | How to change |
|---|---|---|
| `CHAT_RATE_LIMIT` env var | `60/minute` | Set to any `limits`-format string, e.g. `10/minute`, `100/hour` |

Requests that exceed the limit receive `HTTP 429 Too Many Requests` with a `Retry-After` header.

See [ADR-005](../../docs/adr/ADR-005-rate-limiting-chat.md) for the architectural rationale.

## Running

```bash
cd apps/api
PYTHONPATH=../../packages uvicorn app.main:app --reload --port 8000
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `CHAT_RATE_LIMIT` | `60/minute` | Rate limit for `POST /chat` |

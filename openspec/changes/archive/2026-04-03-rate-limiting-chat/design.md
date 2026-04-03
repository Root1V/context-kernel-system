# Design — rate-limiting-chat

## Approach

Use `slowapi` as the rate limiting layer. It integrates with FastAPI via a middleware and a `@limiter.limit()` decorator on individual routes. The key (client identifier) defaults to the remote IP extracted from the request.

## Dependencies

```
uv add slowapi
```

`slowapi` depends on `limits` (already a transitive dep in many stacks). Uses in-memory storage by default — no external services required.

## Architecture

```
Request → FastAPI middleware (SlowAPI) → route handler
                    ↓ (if limit exceeded)
              429 Too Many Requests
              Retry-After: <seconds>
```

## File Changes

### `apps/api/app/main.py`
- Instantiate `Limiter` with key function `get_remote_address`
- Set `app.state.limiter = limiter`
- Add `SlowAPIMiddleware` to app
- Register the `_rate_limit_exceeded_handler` exception handler for `RateLimitExceeded`

### `apps/api/app/routes/chat.py`
- Import `limiter` from the app state (or a shared module)
- Decorate `chat()` with `@limiter.limit(settings.CHAT_RATE_LIMIT)`
- Add `request: Request` parameter to the handler signature (required by slowapi)

### `apps/api/app/config.py`
- Add `CHAT_RATE_LIMIT: str = "60/minute"` read from env var

### `apps/api/tests/test_rate_limit.py` (new)
- Test that requests within the limit return 200
- Test that the (N+1)th request returns 429
- Test `Retry-After` header is present on 429

## Rate Limit Key

`get_remote_address` from `slowapi.util` — extracts `X-Forwarded-For` or falls back to `request.client.host`. Appropriate for a local/dev API behind a single proxy layer.

## Configuration

| Env var | Default | Example values |
|---|---|---|
| `CHAT_RATE_LIMIT` | `60/minute` | `10/minute`, `100/hour`, `5/second` |

## 429 Response Shape

```json
HTTP 429 Too Many Requests
Retry-After: 42
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1743700800

{"error": "Rate limit exceeded: 60 per 1 minute"}
```

The body format is provided automatically by `slowapi`'s default error handler.

## What Does NOT Change

- `ChatRequest` / `ChatResponse` schemas — unchanged
- Orchestration logic — unchanged
- All other routes (`/sessions`, `/health`) — no rate limiting applied

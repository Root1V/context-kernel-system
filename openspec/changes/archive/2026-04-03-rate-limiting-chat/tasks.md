# Tasks — rate-limiting-chat

## Implementation Tasks

- [x] **T1** — Add `slowapi` dependency
  - Run `uv add slowapi` from the repo root
  - Verify `slowapi` appears in `pyproject.toml` dependencies

- [x] **T2** — Add `CHAT_RATE_LIMIT` to config
  - File: `apps/api/app/config.py`
  - Add `CHAT_RATE_LIMIT: str` field reading from env var, default `"60/minute"`

- [x] **T3** — Configure limiter in `main.py`
  - File: `apps/api/app/main.py`
  - Instantiate `Limiter(key_func=get_remote_address)`
  - Set `app.state.limiter = limiter`
  - Add `app.add_middleware(SlowAPIMiddleware)`
  - Register `_rate_limit_exceeded_handler` for `RateLimitExceeded`

- [x] **T4** — Apply rate limit decorator to chat route
  - File: `apps/api/app/routes/chat.py`
  - Add `request: Request` parameter to `chat()` handler
  - Add `@limiter.limit(...)` decorator referencing `CHAT_RATE_LIMIT` from config

- [x] **T5** — Write tests for rate limiting
  - File: `apps/api/tests/test_rate_limit.py` (new)
  - Test: requests within the limit return `200`
  - Test: request exceeding the limit returns `429`
  - Test: `429` response includes `Retry-After` header

- [x] **T6** — Run quality gate
  - Run `bash .git/hooks/pre-push`
  - All checks must pass: ruff lint, ruff format, mypy, all 10 test suites

## Task Order

T1 → T2 → T3 → T4 → T5 → T6

Each task depends on the previous. Do not skip T6.

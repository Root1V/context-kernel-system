## ADDED Requirements

### Requirement: API layer validates and delegates — no business logic
The API layer SHALL validate incoming HTTP request payloads using Pydantic request schemas and delegate all processing to the orchestrator. It MUST NOT contain context-assembly, memory, or retrieval logic.

#### Scenario: POST /chat triggers orchestrator
- **WHEN** a valid `POST /chat` request is received with `session_id` and `message`
- **THEN** the API calls `orchestrate(TurnRequest(...))` and returns the `TurnResponse` serialized as JSON with status 200

#### Scenario: Invalid payload returns 422
- **WHEN** a `POST /chat` request is missing the required `message` field
- **THEN** the API returns HTTP 422 with a validation error body, without calling the orchestrator

#### Scenario: GET /health returns service status
- **WHEN** `GET /health` is called
- **THEN** the API returns `{"status": "ok"}` with HTTP 200 if all dependencies are reachable

### Requirement: Sessions are created and retrievable via API
The API SHALL expose `POST /sessions` to create a new session and `GET /sessions/{session_id}` to retrieve session metadata. Session creation MUST trigger initialization of session state via the state service.

#### Scenario: New session is created with a unique ID
- **WHEN** `POST /sessions` is called
- **THEN** a new `session_id` (UUID) is returned and session state is initialized in the state service

#### Scenario: Retrieving non-existent session returns 404
- **WHEN** `GET /sessions/{session_id}` is called with a session_id that does not exist
- **THEN** the API returns HTTP 404 with a descriptive error message

### Requirement: API does not hold application state between requests
All per-request context (session state, memory) SHALL be loaded from the state service on every request. The FastAPI app MUST be stateless and horizontally scalable.

#### Scenario: Two requests for the same session on different workers return consistent state
- **WHEN** two concurrent requests for the same `session_id` are routed to different worker processes
- **THEN** both read session state from the shared database and operate on the same state version

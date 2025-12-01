# API Spec

Base path: `/api`
Content type: `application/json`
Auth: none (anonymous MVP).

## General Behaviors
- Idempotency: start creates a new game each call (not idempotent). Moves are not idempotent but duplicates are rejected with 400. Quit is idempotent.
- Concurrency: server enforces per-game ordering; concurrent calls to the same `game_id` may be rejected with a conflict if state already advanced.
- Validation & limits: `BOARD_SIZE` default 10 (0-indexed coordinates `0..BOARD_SIZE-1`); payloads must be < 1KB; invalid/bounds/finished-game requests return structured errors.
- Error response shape (all endpoints):
  ```json
  {
    "error_code": "invalid_coordinates|duplicate_move|game_not_found|game_finished|model_not_ready|capacity_exceeded|invalid_payload",
    "message": "human-readable summary",
    "details": { "field": "x", "reason": "must be between 0 and 9" }
  }
  ```

## POST /games
- Description: Start a new game session. Supports player type selection and optional bot-vs-bot auto-play.
- Request (all fields optional):
  ```json
  {
    "placements": [ { "name": "Carrier", "coordinates": [[0,0], [1,0], [2,0], [3,0], [4,0]] } ],
    "config": {
      "player_type": "human|random_bot|heuristic_bot|dqn_agent",
      "agent_type": "random_bot|heuristic_bot|dqn_agent",   // human agent is rejected
      "auto_play": false                                     // when true, both sides must be bots; game runs to completion server-side
    }
  }
  ```
- Responses:
  - 200:
  ```json
  {
    "game_id": "uuid",
    "board": {...},        // player view
    "agent_board_masked": {...}, // masked agent board for client (if exposed)
    "status": "in_progress|player_won|agent_won|aborted",
    "player_type": "human",
    "agent_type": "dqn_agent",
    "auto_play": false,
    "model_version": "v1.0.0",
    "model_hash": "sha256..."
  }
  ```
  - 429: `{ "error_code": "capacity_exceeded", ... }` when `MAX_ACTIVE_GAMES` cap is hit.
  - 503: `{ "error_code": "model_not_ready", ... }` when model failed to load/readiness not met.

## POST /games/{game_id}/moves
- Description: Submit a player move and receive the agent response.
- Request:
  ```json
  {
    "x": 0,
    "y": 0
  }
  ```
- Validation: reject out-of-bounds, duplicates, finished games.
- Response 200:
  ```json
  {
    "player_result": {"outcome": "hit|miss|sunk", "ship": "optional"},
    "agent_move": {"x": 5, "y": 3, "outcome": "hit|miss|sunk", "ship": "optional"},
    "board": {...},          // updated player-visible board
    "agent_board_masked": {...},
    "status": "in_progress|player_won|agent_won"
  }
  ```
- Error responses:
  - 400: `{ "error_code": "invalid_coordinates|duplicate_move|invalid_payload" }`
  - 404: `{ "error_code": "game_not_found" }`
  - 409: `{ "error_code": "game_finished" }`
  - 503: `{ "error_code": "model_not_ready" }` (inference/model load failure)

## POST /games/{game_id}/quit
- Description: End a game early.
- Request: none.
- Responses:
  - 200:
  ```json
  {
    "status": "ended"
  }
  ```
  - 404: `{ "error_code": "game_not_found" }`
  - 409: `{ "error_code": "game_finished" }` if already finished (idempotent on quit).

## GET /health/live
- Description: Liveness probe.
- Response 200: `{ "status": "ok" }`

## GET /health/ready
- Description: Readiness probe.
- Response 200: `{ "status": "ready", "model_version": "vX", "model_hash": "...", "device": "cpu|cuda" }`
- Response 503 with error details when model failed to load, missing artifact, hash mismatch, configuration invalid, or critical dependencies unavailable.

## Trainer lifecycle
- `POST /api/training/runs`: start a trainer run. Body: `{ "config": { ... } }` (optional). Response: `{ "run_id": "...", "status": "pending|running|succeeded|failed|canceled", "config": {...}, "error": null }`.
- `GET /api/training/runs/{id}`: fetch run status.
- `POST /api/training/runs/{id}/cancel`: cancel an in-flight run.
- `GET /api/training/runs/{id}/metrics`: return metrics for the run (episodes, win_rate, loss, curriculum_phase, etc.).
- Errors: `training_not_found` (404) for unknown run ids, `invalid_payload` (400) for bad requests.

## Rate Limits & Backoff (planned)
- No rate limits in MVP, but clients should support `429` with backoff.
- Active game cap (`MAX_ACTIVE_GAMES`) may return `429`; clients should surface a friendly retry message.

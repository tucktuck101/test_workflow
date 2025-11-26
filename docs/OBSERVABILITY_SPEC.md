# Observability Spec

## Metrics
- Request latency and counts for start/move/quit endpoints (by status/outcome).
- RL inference latency and error counts.
- Validation failures (out-of-bounds, duplicate, finished-game).
- Active games and game completions (player_won/agent_won/quit).
- Model load status/version labels on readiness metrics.

## Logs
- Structured logs for requests, validation errors, RL inference errors, and game-end summaries (no PII).
- Include `game_id`, endpoint, outcome, model_version; avoid coordinates in logs unless needed for debugging.

## Tracing
- Trace spans for request handling and RL inference calls; include game_id (non-PII) and outcome tags.
- Annotate inference spans with model_version and device (cpu|cuda).

## Health/Readiness
- `/health/live` (process up) and `/health/ready` reflecting model load status and critical dependencies; readiness returns version/hash on success.

## SLOs / SLIs (initial)
- **SLI:** Turn handling success rate (2xx) and p95 latency for `/api/games/{id}/moves` (player move + agent response).
- **SLO (draft):** p95 latency target ≤ 500ms in dev; tighten after load testing. Success rate ≥ 99% excluding client errors.
- **SLI:** RL inference p95 latency and error rate.
- **SLO (draft):** p95 inference latency ≤ 200ms; revisit after baseline.
- **SLI:** Readiness success rate (model load) over 5-minute windows.
- **SLO (draft):** Readiness success ≥ 99.9% during normal operation.

## Operational Notes
- Primary impacted operations: start game, player move (includes inference), quit game. Each MUST have at least one metric, structured log, and trace span covering the operation.
- Dashboards/alerts should watch turn-handling latency/success, inference latency/error rate, and readiness.
- Update SLO thresholds and alert policies whenever gameplay latency budgets or model performance characteristics change.

## Instrumentation Plan
- Libraries: OpenTelemetry (metrics/traces) with stdout/exporter placeholders; structured logging (json or key-value) via standard logger.
- Per-operation mapping:
  - Start game: log validation results and game_id; metrics `games_started_total`, `games_start_latency_ms` with status label; trace span `game.start`.
  - Move: log validation failures and outcomes; metrics `moves_total` (by outcome), `move_latency_ms` (histogram), `rl_inference_latency_ms`, `active_games`; trace spans `game.move` and child span `inference.call` with model_version/device.
  - Quit: log termination reason; metric `games_quit_total`; trace `game.quit`.
  - Health/ready: gauge `model_ready` (0/1) labeled with version/hash/device; readiness failures logged once per transition.
- Cardinality: allow `game_id` tag in logs and traces; avoid high-cardinality fields (no coordinates, payloads). Limit status/outcome labels to small enums.
- Sampling: keep tracing sampling low but deterministic in tests; configurable sampling rate via env for prod-like runs.

## Alerts (draft)
- Alert if move p95 latency > 500ms for 5 minutes (dev baseline), inference error rate > 1%, or readiness fails for >2 minutes.
- Page/block PR if `model_ready` = 0 on startup; surface in CI smoke tests.

# Observability Spec

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: metrics naming, exporter changes, tracing changes, alert policy changes.

## Current Truth
The backend has observability scaffolding and documented metric/log/trace intent. Dashboard and alert definitions are still documentation-level stubs until concrete exporter/rule/dashboard artifacts are added.

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

## SLOs / SLIs (partial, baseline-first)
- **SLI:** Turn handling success rate (2xx) and p95 latency for `/api/games/{id}/moves` (player move + agent response).
- **SLO (partial):** p95 latency target ≤ 500ms in dev; tighten after load testing. Success rate ≥ 99% excluding client errors.
- **SLI:** RL inference p95 latency and error rate.
- **SLO (partial):** p95 inference latency ≤ 200ms; revisit after baseline.
- **SLI:** Readiness success rate (model load) over 5-minute windows.
- **SLO (partial):** Readiness success ≥ 99.9% during normal operation.

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

## Alerts (partial)
- Alert if move p95 latency > 500ms for 5 minutes (dev baseline), inference error rate > 1%, or readiness fails for >2 minutes.
- Page/block PR if `model_ready` = 0 on startup; surface in CI smoke tests.

## Dashboard & Alert Stubs (initial)
- Panels (Grafana-style):
  - Request rate/latency (p50/p95) for `/api/games` start and moves (stacked by status).
  - RL inference latency histogram and error rate.
  - Active games (gauge) and completions by outcome.
  - Readiness state (model_ready) with version/hash labels.
  - Backend resource utilization (CPU/mem) for container/pod.
- Alerts (fast/slow burn):
  - Slow burn: move p95 > 500ms for 15m.
  - Fast burn: inference error rate > 1% for 5m.
  - Readiness failing > 2m (model_ready = 0).
  - Capacity nearing cap: active_games > 90% of `MAX_ACTIVE_GAMES`.
- Ownership: Backend/infra team; page operator; warn-only for capacity/readiness in dev. Tune thresholds after baseline load test.

## Implemented
- Health/readiness endpoint behavior and readiness model metadata.
- Observability-oriented route spans and metric recording points in backend source.
- Documentation for runtime and ML lifecycle metrics, logs, traces, alerts, and dashboard panels.

## Planned
- Stable exporter configuration and metric naming contract.
- Stored dashboard definitions or screenshots.
- Concrete alert rule files with owners and IDs.
- Baseline load-test data to replace draft SLO thresholds.

## Roadmap
- Keep this spec aligned with `docs/operations/SLOS.md`, `docs/operations/ALERTING.md`, and `docs/operations/DASHBOARDS.md`.
- Treat all thresholds as draft until measured baselines are recorded in `docs/VERIFICATION.md` or a linked evidence note.

## Verification
Reconciled on 2026-04-25 against backend route behavior, health/readiness source, current operations docs, and `docs/VERIFICATION.md`.

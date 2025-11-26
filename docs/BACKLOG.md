# Backlog (Stage 4 Planning)

Link requirements/ADRs: VISION, REQUIREMENTS, USER_STORIES, ADR-0001, ADR-0002, ADR-0003.
Tag scheme: `epic-<id>-start`, `epic-<id>-feature-<name>-done`, `epic-<id>-complete`.

## Epics
- **EPIC-001: MVP Gameplay & RL Opponent**
  - Goal: Deliver backend gameplay API, RL inference path (stub + model load), frontend play loop, and baseline observability/tests to meet MVP requirements.
  - Done when: start/move/quit flows are playable end-to-end with deterministic tests, readiness tied to model load, and coverage/obs gates met.

- **EPIC-002: Training Pipeline Bootstrap**
  - Goal: Stand up offline training pipeline skeleton, produce versioned artifacts, and document promotion/validation; does not expose live training in runtime.
  - Done when: training job builds an artifact + manifest with hash/version and can be consumed by runtime load path; docs/runbooks updated.

## Features and Tasks (EPIC-001)
- **F1: Backend Gameplay API (FastAPI)**
  - T1: Scaffold FastAPI service with config/env validation (BOARD_SIZE, MODEL_PATH/VERSION/HASH/DEVICE, DETERMINISTIC_MODE, MAX_ACTIVE_GAMES). Acceptance: invalid/missing envs fail fast; config documented.
  - T2: Implement game engine (board setup, move validation, status transitions, duplicate/finished-game guards). Acceptance: unit tests cover rules, duplicate/out-of-bounds, win/quit.
  - T3: Implement API routes `/api/games`, `/api/games/{id}/moves`, `/api/games/{id}/quit` with structured errors (400/404/409/429/503). Acceptance: contract tests for happy/invalid/finished/capacity/model-not-ready.
  - T4: Add health endpoints `/health/live`, `/health/ready` tied to model load/hash verification. Acceptance: readiness fails on missing/mismatch; smoke tests cover pass/fail.

- **F2: RL Inference Adapter**
  - T5: Implement deterministic/stubbed agent path gated by `DETERMINISTIC_MODE`; seedable for tests. Acceptance: tests assert deterministic outputs.
  - T6: Integrate real model load (PyTorch) with hash verification and device selection (cpu default, cuda optional). Acceptance: readiness reflects load status; inference errors marked and surfaced as 503.

- **F3: Frontend Play Loop**
  - T7: Scaffold React+Vite app with board UI, move submission, and status/error handling. Acceptance: start/play/quit flows exercised against API; basic component tests.
  - T8: Add API client layer with retries/backoff handling 400/404/409/429/503; show user-friendly errors. Acceptance: UI surfaces error states; tests cover error rendering.

- **F4: Quality Gates (Tests/Obs/Security)**
  - T9: Add metrics/logs/traces per OBSERVABILITY_SPEC (start/move/quit, inference). Acceptance: metrics emitted; traces/logs include game_id and model metadata; no secrets.
  - T10: Expand test suites to meet coverage targets (engine ≥90%, backend 85–90%, frontend 70–80%), include API contract tests, and load-test script stub (k6/Locust) documented. Acceptance: CI passing with coverage thresholds; load test plan/script present.
  - T11: Wire pre-commit hooks and CI jobs to stack specifics (npm/pytest/mypy). Acceptance: `ci/run_quality_gates.sh` recognizes project scripts; CI green.

## Features and Tasks (EPIC-002)
- **F5: Training Pipeline Skeleton**
  - T12: Create training job scaffold (PyTorch) with config/seed control and simple dataset stub. Acceptance: script trains a trivial model and writes artifact + manifest (version/hash/device).
  - T13: Document promotion flow (artifact storage, hash, versioning) and update runbooks/DEPLOYMENT accordingly. Acceptance: runbook entry covers promotion/rollback.
  - T14: Add validation step for artifact integrity (hash) before runtime consumption; align with readiness. Acceptance: documented and testable hash check flow.

## Board & Tracking Guidance
- Columns: Backlog → Ready → In Progress → In Review → Ready for Human Review → Done.
- Labels: Epic, Feature, Task, Bug, Tech Debt, Refactor, Incident, BLOCKER. Add risk labels if desired (low/medium/high/regulated).
- Each Issue: include acceptance criteria, linked requirements/ADRs, risk level, task tier, and Quality Gate row. Ensure Critic Pass note before merge.

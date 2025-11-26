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
  - **T1: Scaffold FastAPI service + config/env validation**
    - Steps: create backend skeleton; parse/validate envs (`BOARD_SIZE`, `MODEL_PATH/VERSION/HASH/DEVICE`, `DETERMINISTIC_MODE`, `MAX_ACTIVE_GAMES`, `LOG_LEVEL`, `OBSERVABILITY_ENABLED`); fail fast on missing/invalid; add config tests.
    - DoD: config tests pass; `.env.example`/CONFIGURATION updated; CODE_MAP updated; CI scripts aware of backend commands.
  - **T2: Game engine rules**
    - Steps: implement board setup/ship placement, move validation, status transitions, duplicate/finished-game guards; add deterministic seeding helper.
    - DoD: unit tests cover bounds, duplicates, win/quit paths; coverage ≥90% for engine module; CODE_MAP updated.
  - **T3: Gameplay API routes**
    - Steps: add `/api/games`, `/api/games/{id}/moves`, `/api/games/{id}/quit`; structured errors (400/404/409/429/503); capacity check for `MAX_ACTIVE_GAMES`.
    - DoD: contract/API tests for happy/invalid/finished/capacity/model-not-ready; OpenAPI/docs updated; coverage ≥85% backend; obs/log hooks called.
  - **T4: Health endpoints**
    - Steps: implement `/health/live` and `/health/ready` tied to model load/hash; add smoke tests for pass/fail states; wire readiness to model adapter.
    - DoD: readiness returns version/hash/device; tests for missing/mismatch; CI coverage unchanged; docs updated.

- **F2: RL Inference Adapter**
  - **T5: Deterministic/stubbed agent**
    - Steps: implement stub agent gated by `DETERMINISTIC_MODE`; seed control; expose predictable outputs for tests.
    - DoD: unit tests verify deterministic outputs; TEST_STRATEGY updated; no secrets/logs; coverage met.
  - **T6: Real model load/inference**
    - Steps: integrate PyTorch load with SHA256 check and device selection; error handling marking model not ready; inference wrapper with typed errors.
    - DoD: readiness reflects load status; tests for good/missing/mismatch; 503 surfaced on inference failure; OBSERVABILITY_SPEC hooks implemented.

- **F3: Frontend Play Loop**
  - **T7: React/Vite scaffold + board UI**
    - Steps: scaffold app; implement board display, start/quit actions, move submission; basic routing/state mgmt.
    - DoD: component tests for render/state; start/play/quit happy path against mocked API; coverage 70–80% frontend.
  - **T8: API client layer + error UX**
    - Steps: create API client handling 400/404/409/429/503 with backoff; surface user-friendly errors; deterministic test fixtures.
    - DoD: tests cover error rendering/retries; no secrets in logs; docs updated for error behaviors.

- **F4: Quality Gates (Tests/Obs/Security)**
  - **T9: Metrics/logs/traces**
    - Steps: instrument start/move/quit and inference per OBSERVABILITY_SPEC; structured logs with `game_id`, model metadata; tracing spans added.
    - DoD: metrics/traces/logs observable in local run; tests assert emission where feasible; docs kept in sync.
  - **T10: Tests/coverage + load test stub**
    - Steps: expand suites to meet coverage targets (engine ≥90%, backend 85–90%, frontend 70–80%); add API contract tests; add k6/Locust stub and doc.
    - DoD: CI coverage thresholds met; load test script documented; no >2pp drop on touched components.
  - **T11: CI/pre-commit wiring**
    - Steps: add npm/pytest/mypy scripts; ensure `ci/run_quality_gates.sh` calls them; update CI workflow if needed.
    - DoD: CI green running format/lint/tests/type checks; pre-commit configured for stack; docs updated.

## Features and Tasks (EPIC-002)
- **F5: Training Pipeline Skeleton**
  - **T12: Training job scaffold**
    - Steps: create training script with config/seed control and simple dataset stub; produce artifact + manifest (version/hash/device).
    - DoD: script runs locally; artifact + manifest written; tests for manifest/hash generation; coverage target met for module.
  - **T13: Promotion flow docs/runbook**
    - Steps: document artifact storage, hash/versioning, promotion/rollback; update DEPLOYMENT/RUNBOOKS.
    - DoD: docs updated with clear steps; no code changes; promotion/rollback examples included.
  - **T14: Artifact validation path**
    - Steps: add validation step for artifact integrity pre-runtime; align readiness checks; tests for hash validation flow.
    - DoD: validation documented and testable; readiness doc updated; coverage maintained.

## Epic Execution Plans
- **EPIC-001 Critical Path:** T1 → T2 → T3 → T4 → T5/T6 (parallel after T1/T2) → T7/T8 (after API stable) → T9/T10/T11 to finalize gates. Parallelizable: T5 with T2; T7 with T3/T4 once API contract stable; T9/T10 with later tasks to meet gates.
- **EPIC-002 Critical Path:** T12 → T14 (validation) → T13 (docs/promotion). Can begin after EPIC-001 readiness/model interface stable but training scaffold can start earlier if decoupled.

## Board & Tracking Guidance
- Columns: Backlog → Ready → In Progress → In Review → Ready for Human Review → Done.
- Labels: Epic, Feature, Task, Bug, Tech Debt, Refactor, Incident, BLOCKER; risk: low/medium/high/regulated.
- Each Issue: include acceptance criteria, linked requirements/ADRs, risk level, task tier, Quality Gate row, DoD (tests/coverage/obs/docs/CI), dependencies, and Critic Pass reminder.

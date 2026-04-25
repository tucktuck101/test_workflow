# Backend Agent Guide

## Purpose
Use this guide for changes under `app/`. The root `AGENTS.md` still applies; this file only adds backend-specific source truth, checks, and caveats.

## Local Source Truth
- `main.py` wires the FastAPI app, settings, model loader, observability, and routers.
- `routes.py` owns gameplay, model, training, and health route registration.
- `schemas.py` defines API request and response contracts, including training run response shapes.
- `engine.py` owns Battleship rules, session state, ship placement, moves, quit behavior, and the in-memory session store.
- `agent.py`, `model_loader.py`, `health.py`, `rate_limit.py`, and `obs.py` support inference, readiness, rate limiting, and telemetry behavior.
- `trainer_orchestrator.py` is the source of truth for training run lifecycle behavior exposed through the API.

## Editing Guidance
- Keep route behavior, schemas, structured errors, and tests aligned when changing public API behavior.
- Verify model readiness claims against `health.py`, `model_loader.py`, and settings, not docs alone.
- Verify gameplay state changes against `engine.py`; avoid duplicating rules in route code unless the existing pattern requires it.
- Treat trainer orchestration as simulated/abstracted unless `trainer_orchestrator.py` proves otherwise. Current compose and Kubernetes orchestrators delegate to dummy behavior.
- Preserve in-memory assumptions unless the task explicitly adds persistence.

## Focused Checks
- Route or schema changes: `make backend-test` or targeted `pytest` for `tests/test_routes.py`, `tests/test_trainer_routes.py`, and related tests.
- Health/readiness changes: targeted `pytest tests/test_health.py`.
- Engine/session changes: targeted `pytest tests/test_engine.py tests/test_session_store.py`.
- Rate limit changes: targeted `pytest tests/test_rate_limit.py`.
- Shared typing or broad backend changes: `make backend-typecheck` when practical.

## Docs Triggers
- Update `docs/API_SPEC.md` when endpoint shape, status codes, or error payloads change.
- Update `docs/CURRENT_STATE.md` only when a verified runtime fact changes.
- Update `CODE_MAP.md` if backend entrypoints, boundaries, or command surfaces change.

## Pitfalls
- Do not present API-triggered training as real local, Compose, or Kubernetes job execution without replacing the current placeholder path.
- Do not treat generated artifacts under `artifacts/` as backend source truth.
- Avoid broad test runs by reflex; pick focused checks that cover the changed behavior.

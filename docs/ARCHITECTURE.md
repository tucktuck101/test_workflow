# Architecture

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: module boundary, runtime flow, deployment, or orchestration changes.

## Current Truth
The architecture is a local-first full-stack ML training and inference environment. Runtime gameplay and model readiness paths are active. Training APIs model run lifecycle state, but job execution is currently simulated/placeholder-backed.

## System Classification
- Full-stack web app with RL agent-driven gameplay.
- Components: frontend (React/TypeScript), backend API (Python/FastAPI), RL inference module (static model), separate training pipeline (PyTorch).

## High-Level Components
- Frontend UI: renders homepage and game board, sends start/move/quit requests, displays agent responses. Talks to backend via REST; no game logic trusted on client.
- Backend API: authoritative game engine (rules, validation), session/state management (initially in-memory), interfaces with RL inference for opponent moves. Provides health endpoints.
- RL Inference Module: loads static trained model artifact; serves move decisions via in-process call to avoid network hops; supports CPU/GPU. Deterministic test mode uses seeded/stubbed policy.
- Training Pipeline (separate environment): trains RL model until satisfactory, outputs versioned artifacts for runtime deployment. Produces metadata (version/hash/timestamp) for runtime integrity checks.

## Backend Module Boundaries
- API Layer (FastAPI): routing, request validation, response shaping, status codes; houses health/live/ready endpoints.
- Game Engine: board setup, rules, move adjudication, win/quit handling, validation (bounds, duplicate prevention, finished-game rejection).
- Session Store: in-memory map keyed by `game_id`, capped by `MAX_ACTIVE_GAMES`; TTL/cleanup on quit/finish/timeout.
- Agent Adapter: wraps RL model load/selection, device choice, deterministic/stubbed path, and inference call; surfaces typed errors for readiness/turn handling.
- Observability Layer: structured logging, metrics, traces; attaches `game_id`, outcome, model metadata; enforces no-secrets logging.
- Configuration Layer: env parsing and validation for model path/hash/device, board size, observability toggles, deterministic mode, and concurrency caps.

## Data & State
- MVP: in-memory game/session state on the backend; no persistent user identity. Game map is authoritative on server; client gets masked agent board only.
- Model artifacts: stored locally for dev; to be mounted/packaged for k8s deployment. Runtime records `MODEL_VERSION`, `MODEL_HASH`, and load status for readiness.
- Future persistence (post-MVP): database (e.g., Postgres) for game history, accounts, leaderboards.

## Environments
- dev, test, prod (runtime), plus training (isolated). Local-first; Kubernetes-ready manifests/overlays later.
- Training runs offline; runtime consumes static model artifacts. Runtime disallows on-the-fly training.

## Interaction/Flows
- Start Game: frontend → API `/api/games` (POST) → config/limits check (active game cap) → create session (seeded board, ships placed, deterministic seed if set) → return `game_id`, masked agent board, status. Cleanup if session creation fails.
- Player Move: frontend → API `/api/games/{id}/moves` (POST) → validate game existence/status/bounds/duplicates → apply player move to authoritative board → call Agent Adapter (deterministic stub in tests) → apply agent move → update statuses → return both outcomes, updated masks, status. If inference fails, mark game aborted and return 503 with cleanup.
- Quit: frontend → API `/api/games/{id}/quit` (POST) → mark session ended, release memory; idempotent.
- Health: `/health/live` reflects process up; `/health/ready` fails if model missing/hash mismatch/load failure or configuration invalid.
- Error handling: 400 for validation errors; 404 for unknown game; 409 for finished games; 429 planned for rate-limit/cap hits; 503 for inference/model readiness failures.

## Nonfunctional Considerations
- Testing: high coverage on rules and agent integration; load testing for move endpoints; deterministic inference path or stub for tests.
- Observability: metrics/logging/tracing on move latency, RL inference latency, validation failures, session counts; include `game_id` tags (non-PII).
- Security: baseline posture; input validation, rate-limit readiness for future, dependency/secrets scanning; model artifacts integrity-checked with hash.
- Deployment: containerize backend and frontend; enable GPU where available for training/inference; monorepo with shared CI; readiness tied to model load.

## Reference Standards Alignment
- **OWASP/ASVS:** strict input validation (bounds, duplicates, status checks); no client trust; readiness fails on model integrity issues; path validation for artifacts; plan for rate limiting/active-game caps to deter abuse; health/readiness avoid leaking internals.
- **12-Factor:** config via envs; explicit dependency management; backing services (model artifacts) bound via config; port binding; stateless processes aside from in-memory MVP state with planned externalization; logs as structured streams; disposability supported via readiness tied to model load.
- **Determinism & Limits:** `DETERMINISTIC_MODE` gates stubbed agent for tests/debug; seeded boards for repeatability; `MAX_ACTIVE_GAMES` enforces memory cap; planned 429 for cap/rate exceedance.
- **Failure Modes:** inference/model errors fail fast and mark sessions aborted; cleanup on quit/finish/error; readiness blocks traffic until model load verified.

## Implemented
- FastAPI runtime with gameplay, model, health, readiness, and training lifecycle routes.
- React/Vite gameplay UI and separate React/Vite training UI.
- Offline training modules, configs, artifact validation, smoke scripts, and container definitions.
- In-memory gameplay sessions and in-memory simulated training run state.

## Planned
- Process-backed local trainer orchestration behind the API.
- Compose and Kubernetes trainer adapters that launch real isolated jobs.
- Production-grade telemetry pipeline, dashboard artifacts, and alert rules.
- Future persistence for game history, accounts, or leaderboards.

## Roadmap
- Keep architecture claims tied to source modules and container configuration.
- Replace text-only portfolio diagrams with maintained diagrams after module boundaries stabilize.
- Move orchestration capability status only after `app/trainer_orchestrator.py` launches real jobs.

## Verification
Reconciled on 2026-04-25 against `CODE_MAP.md`, `app/routes.py`, `app/trainer_orchestrator.py`, frontend entrypoints, training directories, and Docker Compose.

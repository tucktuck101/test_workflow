# Battleships RL Platform

This repository uses Battleships as a controlled RL/AI training platform. The portfolio focus is training agents, validating and promoting model artifacts, serving inference, and applying SRE/Platform Engineering practices around the training and runtime delivery system.

The implementation is active: FastAPI backend, React/Vite gameplay UI, React/Vite training UI, training modules, containers, smoke paths, and tests are present. Some older planning and governance docs remain useful as history, but they may be stale. For Codex/project navigation, start with `AGENTS.md` and `docs/CURRENT_STATE.md`.

## What Is Here
- Backend API in `app/`: gameplay routes, model routes, health/readiness, session state, rate limiting, and training run endpoints.
- Gameplay frontend in `frontend/src/App.tsx`: board UI, readiness/model metadata, ship placement, human play, bot types, and auto-play wiring.
- Training UI in `frontend/src/TrainingControl.tsx`: training config form, curriculum editing, run lifecycle actions, and metrics polling.
- Training pipeline in `training/`: environment, policies, DQN/self-play, curriculum, evaluation, artifact generation, and validation support.
- Runtime packaging in `docker-compose.yml`, `Dockerfile.*`, and `k8s/`.
- Tests in `tests/`, `frontend/src/*.test.*`, and `frontend/e2e/`.

## Portfolio Story
- `docs/portfolio/CASE_STUDY.md`: portfolio framing and current evidence.
- `docs/portfolio/ML_PIPELINE_STORY.md`: training, artifact, validation, promotion, and serving narrative.
- `docs/portfolio/SRE_PLATFORM_STORY.md`: SRE/Platform practices around inference and training operations.
- `docs/DEMO_PATH.md`: intended fresh-checkout demo flow and current caveats.

## Start Here
For future Codex work:

1. Read `AGENTS.md`.
2. Run `git status --short --branch`.
3. Inspect changed files before editing.
4. Use `rg --files` and targeted `rg` searches to find current source truth.
5. Treat older docs as historical until verified against code/tests/config.

For humans, `docs/CURRENT_STATE.md` gives a compact snapshot of the current implementation.

## Common Commands
- `make setup`: create a Python venv, install Python requirements, and install frontend dependencies.
- `make verify-local`: run the local dev/test parity checks used before opening a PR.
- `make backend-test`: run Python tests.
- `make backend-coverage`: run backend coverage checks.
- `make frontend-test`: run Vitest with coverage.
- `make train-smoke`: run mini training, validation, and evaluation smoke.
- `make smoke`: run the local smoke script.
- `make smoke-local`: run the CI-safe Docker Compose smoke path with baked stub model config.
- `make run`: build and run the Docker Compose stack.
- `make train`: run DQN self-play using `CONFIG`, defaulting to `configs/dqn_train.yaml`.

Frontend-only commands:

- `cd frontend && npm run dev`
- `cd frontend && npm run build`
- `cd frontend && npm run build:training`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test:e2e`

## Configuration
Runtime configuration is environment-driven. Start with `.env.example` and `CONFIGURATION.md`, then verify current behavior in `app/config.py`, `docker-compose.yml`, and the relevant Dockerfile.

Backend model readiness depends on the configured model path, version, hash, and device. Generated training artifacts should live under `artifacts/` locally and should not be treated as source.

## Documentation Notes
- `docs/README.md`: canonical docs entrypoint and trust/precedence rules.
- `AGENTS.md`: canonical Codex operating guide.
- `docs/CURRENT_STATE.md`: source-verified implementation snapshot.
- `docs/REPOSITORY_BOOTSTRAP.md`: clean GitHub presentation repo and Project setup guide.
- `CODE_MAP.md`: compact subsystem map.
- `docs/portfolio/`, `docs/operations/`, and `docs/ml/`: portfolio-oriented SRE, platform, and ML lifecycle stubs.
- `docs/history/`, `docs/history/governance/`, and `adr/`: governance, design history, and planning context. Verify before relying on them.

## Gameplay Loop
- Start a game from the frontend.
- For human play, place the full fleet and confirm placements.
- Fire on the agent board until one fleet is sunk.
- Bot player types and auto-play are available through the UI/API configuration.

## Artifact Hygiene
Generated outputs are intentionally ignored:

- `artifacts/`
- `frontend/dist/`
- `frontend/dist-training/`
- `frontend/coverage/`
- local caches such as `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.venv/`, and `frontend/node_modules/`

Keep `artifacts/.gitkeep` so the local artifact directory exists in fresh checkouts.

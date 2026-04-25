# Codex Operating Guide

## Project Reality
This is a Battleships AI/ML training environment with SRE/Platform Engineering portfolio material, not a planning-only scaffold. It currently contains a FastAPI backend, a React/Vite gameplay UI, a separate React/Vite training UI entrypoint, offline training modules, Docker Compose services, tests, and several governance/planning docs that may be stale.

Treat this file as the first-read guide for Codex. Treat older planning docs as historical context until their claims are verified against source.

## First Five Minutes
1. Read this file.
2. Run `git status --short --branch`.
3. Inspect changed files before editing, especially in a dirty worktree.
4. Use `rg --files` and targeted `rg` searches to find the current implementation.
5. Read the relevant source, tests, configs, Dockerfiles, and package manifests for the task.
6. Treat older planning/history docs, especially under `docs/history/`, as stale until confirmed against source.
7. Use `docs/README.md` as the canonical docs entrypoint and trust-order guide.

Source-of-truth priority:
1. Current code, tests, configs, Dockerfiles, and package manifests.
2. Recent git diff and commit history.
3. Runtime docs refreshed in the current navigation cleanup, especially `docs/CURRENT_STATE.md`.
4. Planning and governance docs.
5. Generated artifacts, screenshots, diagnostics, and old metrics.

## Active Subsystems
- Backend API: `app/` contains FastAPI app wiring, routes, schemas, health/readiness, model loading, rate limiting, observability scaffolding, session state, and gameplay rules.
- Gameplay frontend: `frontend/src/App.tsx`, `frontend/src/api.ts`, and related tests implement the browser play loop.
- Training UI: `frontend/src/TrainingControl.tsx`, `frontend/src/training.tsx`, and `frontend/training.html` provide the training control surface.
- Training pipeline: `training/`, `configs/`, `scripts/train_smoke.sh`, and `tools/validate_artifact.py` cover training, self-play, curriculum, validation, and evaluation.
- Bots: `bots/scripted_opponents.py` contains scripted opponent policies used by gameplay and training paths.
- Containers and deployment: `docker-compose.yml`, `Dockerfile.*`, and `k8s/` describe local/runtime/trainer packaging.
- Tests: `tests/`, `frontend/src/*.test.tsx`, `frontend/src/*.test.ts`, and `frontend/e2e/` cover backend, training, frontend, and e2e behavior.
- Portfolio docs: `docs/portfolio/`, `docs/operations/`, `docs/ml/`, and `docs/DEMO_PATH.md` frame the SRE/Platform and ML lifecycle story.
- Historical docs: `docs/history/`, `docs/history/governance/`, and `adr/` are useful context but may lag implementation.

## Commands
- `make backend-test`: run the Python test suite.
- `make backend-coverage`: run backend coverage gate.
- `make frontend-test`: run Vitest with frontend coverage.
- `make train-smoke`: run mini training, validation, and eval smoke.
- `make smoke`: run the local smoke script.
- `make run`: build and start the Docker Compose stack.
- `cd frontend && npm run dev`: start gameplay frontend dev server.
- `cd frontend && npm run build`: typecheck and build gameplay frontend.
- `cd frontend && npm run build:training`: typecheck and build training UI.
- `cd frontend && npm run typecheck`: run TypeScript checks only.
- `cd frontend && npm run test:e2e`: run Playwright tests.

Pick focused checks for the files touched. Do not run expensive or broad commands by reflex when a narrower test answers the risk.

## Do Not Waste Time On
Normally ignore generated or local-only paths unless the task is specifically about them:

- `artifacts/`
- `frontend/dist/`
- `frontend/dist-training/`
- `frontend/coverage/`
- `.coverage`
- `.pytest_cache/`
- `.ruff_cache/`
- `.mypy_cache/`
- `.venv/`
- `frontend/node_modules/`
- `git_diag_*`
- `screencaps/`

`docs/history/governance/`, ADRs, and older planning docs are governance/history. Read them only when the task concerns workflow policy, project history, ADRs, or requirements traceability.

## When Editing
- Preserve user changes. Do not revert unrelated dirty files.
- Make the smallest change that handles the task.
- Prefer repo patterns over new abstractions.
- Update `docs/CURRENT_STATE.md` only when a verified repo fact changes.
- Update `CODE_MAP.md` when subsystem boundaries, entrypoints, or command surfaces change.
- Keep generated outputs out of reviews and commits unless explicitly requested.
- For docs-only navigation changes, backend/frontend tests are usually unnecessary; verify with `git diff --stat`, targeted stale-text search, and manual markdown sanity checks.

## Known Project Risks
- Some docs still describe old planning stages and may contradict current source.
- Generated artifact churn can overwhelm reviews if not ignored.
- Trainer orchestration endpoints currently use simulated/local orchestration behavior unless proven otherwise from source.
- Runtime model quality and trained artifact readiness are uncertain.
- Training API orchestration is currently simulated/abstracted; `docs/ml/TRAINING_ORCHESTRATION.md` describes the replacement target.
- Repo structure is likely to change as the project is tidied, so prefer discovery commands over memorized paths.

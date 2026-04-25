# Current State

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: runtime, API, training, deployment, frontend, or testing behavior changes.

This snapshot reflects the repository as verified during the Codex navigation cleanup. If source and this file disagree, trust source and update this file after confirming the new fact.

## Current Truth
This is a Battleships AI/ML training environment with a Python/FastAPI backend, React/Vite browser clients, and offline training code. The app is no longer a planning-only scaffold.

The portfolio story is SRE/Platform Engineering around ML training and inference: train agents in a controlled domain, validate artifacts, promote or roll back model versions, serve inference, and observe runtime/training reliability.

The backend owns gameplay state and rules. It exposes game start/move/quit routes, model listing/loading routes, health/readiness routes, rate limiting, and training run routes. Sessions are in memory. Model readiness is tied to configured artifacts, hash validation, and device/version settings.

The gameplay frontend supports readiness display, model metadata, manual ship placement, human play, bot player types, and auto-play flows. The training frontend is a separate Vite entrypoint focused on training configuration, curriculum editing, run lifecycle actions, and metrics polling.

The training side contains classic trainer code, DQN/self-play code, curriculum handling, vectorized environments, evaluation, artifact validation, and YAML configs.

Training API orchestration is intentionally not described as production orchestration: `app/trainer_orchestrator.py` uses dummy lifecycle behavior for local/dev and placeholder Compose/Kubernetes adapters that delegate to dummy behavior.

## Implemented
- Backend: `app/main.py`, `app/routes.py`, `app/schemas.py`, `app/engine.py`, `app/agent.py`, `app/model_loader.py`, `app/health.py`, `app/rate_limit.py`, `app/trainer_orchestrator.py`.
- Gameplay UI: `frontend/src/App.tsx`, `frontend/src/api.ts`, `frontend/src/types.ts`, `frontend/src/styles.css`.
- Training UI: `frontend/src/TrainingControl.tsx`, `frontend/src/training.tsx`, `frontend/training.html`, `frontend/vite.training.config.ts`.
- Training: `training/`, `configs/`, `scripts/train_smoke.sh`, `scripts/plot_dqn_metrics.py`, `tools/validate_artifact.py`.
- Containers: `docker-compose.yml`, `Dockerfile.backend`, `Dockerfile.frontend`, `Dockerfile.training-frontend`, `Dockerfile.trainer`.
- Tests: `tests/`, `frontend/src/*.test.tsx`, `frontend/src/*.test.ts`, `frontend/e2e/`.
- Portfolio docs: `docs/portfolio/`, `docs/operations/`, `docs/ml/`, `docs/DEMO_PATH.md`.
- Historical docs: `docs/history/`, `docs/history/governance/`, and `adr/`.

## Planned
- Real API-triggered local subprocess training orchestration.
- Compose-backed and Kubernetes-backed trainer job execution from the API path.
- Stored dashboard artifacts and concrete alert rule files.
- Production-grade SLI telemetry pipeline and formal SLO policy gates.
- Verified model quality thresholds for artifact promotion.

## Roadmap
- Planning and governance docs may be stale. Verify claims against code, tests, configs, and recent diffs.
- Training run orchestration is not proven to launch real compose or Kubernetes jobs from the API path; inspect `app/trainer_orchestrator.py` before assuming it does.
- `docs/ml/TRAINING_ORCHESTRATION.md` is the honest source for the planned replacement of simulated orchestration.
- Generated artifacts under `artifacts/` and frontend build outputs should not be treated as source.
- The trained model quality and current runtime artifact readiness are not established by this snapshot.
- The repo structure may be reorganized, so subsystem descriptions are more reliable than exhaustive file lists.

## Generated Or Local-Only Paths
Ignore these during normal code navigation unless the task explicitly involves them:

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

## Verification
Reconciled on 2026-04-25 with source inspection of backend routes/schemas/health/config, trainer orchestration, Docker Compose, `Makefile`, `CODE_MAP.md`, and active docs. See `docs/VERIFICATION.md` for command summaries.

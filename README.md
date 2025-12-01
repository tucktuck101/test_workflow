# Coding Agent Workflow — Battleship RL MVP

## Overview
Production-ready Battleship web app where users anonymously play against a pre-trained RL agent. Local-first, Kubernetes-ready, open-source stack (React/TypeScript frontend, FastAPI/Python backend, PyTorch RL).

## Current Status
- Stage: 4 (Planning). Design/architecture, requirements, and ADRs 0001–0003 are complete. Implementation has not started.
- Profiles: workflow_profile standard, tier standard (ADR-0001). Repo strategy monorepo. Risk level medium.
- Scope priorities: MVP gameplay API + frontend loop → observability/tests → training pipeline bootstrap.

## Key Docs
- Vision/Requirements/User Stories: `docs/VISION.md`, `docs/REQUIREMENTS.md`, `docs/USER_STORIES.md`
- Architecture/Data/API/Test/Obs/Security/Deployment: under `docs/` (see also `docs/BACKLOG.md` for planned work)
- ADRs: `adr/ADR-0001-workflow-profile-and-tier.md`, `adr/ADR-0002-tech-stack-and-runtime-architecture.md`, `adr/ADR-0003-state-and-model-handling.md`
- Planning: `docs/STAGE4_PLANNING.md`, `docs/BACKLOG.md`, `docs/EPIC_LOG.md`
- Configuration/env: `CONFIGURATION.md`, `.env.example`

## Workflow & Quality Gates
- Issues/PRs required; use templates in `.github/`.
- Classify risk_level/tier (default medium/standard) and apply Quality Gates (tests, coverage, security, observability). No coverage drops >2pp on touched components without justification.
- ADRs for material decisions (stack, persistence, infra, cost/guardrails, state model).
- Branch naming: `feature/<desc>`, `fix/<desc>`, `epic/<id>-<desc>`, `proposal/<decision-id>-<desc>` when needed.
- Tags per PROCESS_CHECKLIST: `epic-<id>-start`, `epic-<id>-feature-<name>-done`, `epic-<id>-complete`.
- Critic Pass before merge; red-flag human review for auth/data schema/public API/security-sensitive paths.

## Getting Started (pre-implementation)
1) Install pre-commit: `pip install pre-commit` and run `pre-commit install`. Hooks cover trailing whitespace, EOF, YAML/JSON, secrets, codespell, black, ruff, and prettier.
2) Review env defaults in `.env.example` and CONFIGURATION; adjust when backend exists. A stub artifact is provided at `models/stub_model.bin` with hash `9d282bb3026000b1535a0129145ad46fba61fab5799be1a65928797e61d3006e` and version `stub-v1` for dev/CI readiness.
3) CI: `.github/workflows/ci.yml` runs pre-commit, quality gates via `ci/run_quality_gates.sh` (auto-detects Node/Python projects). Update scripts/tests as code lands. Coverage uses pytest-cov; mypy configured; load test stub in `load_tests/k6_load.js` (manual/nightly).
4) Backend formatting/linting: see `.editorconfig`, `.prettierrc.json`, and `pyproject.toml` for formatter/linter settings (black/ruff/prettier).
5) Frontend: `cd frontend && npm install && npm run dev` (or `npm test` for vitest/RTL). Configure `VITE_API_BASE_URL` in `.env` if hitting a non-default backend.
6) Makefile helpers: `make backend-coverage` (pytest with 90% gate), `make frontend-test` (vitest with thresholds), `make load-test` (k6 stub), `make setup` to bootstrap venv + npm deps. Devcontainer available in `.devcontainer/`.
7) Containers: `make run` (or `docker compose up --build`) builds backend/frontend with the trained model mounted from `./artifacts` (see MODEL_* envs in docker-compose). Frontend served on :3000 pointing to backend service. Ensure `artifacts/model.bin` exists (run `make train` if not).
8) Training stub: `python -m training.trainer` (config via TRAIN_* envs) writes artifact + manifest to `./artifacts` by default; logs progress every `TRAIN_LOG_INTERVAL` episodes (default 10). Defaults now mirror real rules: 10×10 board, full fleet (5/4/3/3/2), adjacency allowed by default (`TRAIN_ALLOW_ADJACENT=true`). If you shrink the board via `TRAIN_BOARD_SIZE`, supply a smaller fleet (via `TrainConfig` in code) or it will error when ships don't fit. See tests/test_training.py for deterministic expectations.
9) Artifact validation: `python -m tools.validate_artifact --artifact <file> --manifest <manifest.json> --root <MODEL_ROOT> --device <cpu|cuda>` for promotion checks. Promotion/rollback steps in `docs/RUNBOOKS.md`.
10) CI helper: manual workflow `.github/workflows/artifact-validate.yml` runs the validation CLI; trigger via Actions → Artifact Validate with artifact/manifest/root/device inputs.
11) Training smoke: `make train-smoke` runs mini-train + validator + eval; CI job `training-smoke` runs the same.
12) Full training via Makefile:
   - `make train` runs DQN self-play using the YAML config at `CONFIG` (default `configs/dqn_train.yaml`), then calls the metrics plotter. Override config path with `CONFIG=<path>`. Env vars can still override YAML values.

### Gameplay loop (frontend)
- Click **Start Game** to enter placement mode, then place your fleet by selecting 17 tiles (5+4+3+3+2). Only your ships are shown.
- Hit **Confirm placements** to start; the agent auto-places its ships and your grid keeps ships visible (`⬢` for unhit).
- Fire by clicking the Agent Board. The game ends when one fleet is sunk; restart repeats the placement flow.
- Ships must follow Battleship rules: each ship is a straight, contiguous line (horizontal or vertical) and ships cannot overlap; use the orientation toggle while placing.

## Structure (see `CODE_MAP.md` for more)
- `docs/`: Design/requirements/test/obs/security/deployment/planning/backlog
- `adr/`: Architecture decisions
- `ci/`: CI helper scripts
- `.github/`: Issue/PR templates and workflows
- `init_codex_project.sh`, `reset_codex_init.sh`: bootstrap helpers

## Next Steps (Stage 4/6)
- Populate Issues/board with Epics/Features/Tasks from `docs/BACKLOG.md` (in progress). Use board columns Backlog → Ready → In Progress → In Review → Ready for Human Review → Done.
- Update CODE_MAP entries as code is scaffolded; update EPIC_LOG per epic milestones.
- Implementation path: backend gameplay API (F1/T1–T4), rate-limit guard, inference adapter (F2/T5–T6), frontend loop (F3), observability/CI/devcontainer (F4/T16+), training pipeline (F5/F6).
- Load testing: see `load_tests/k6_load.js` (manual/nightly; configure BASE_URL).

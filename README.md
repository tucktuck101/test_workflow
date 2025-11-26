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
2) Review env defaults in `.env.example` and CONFIGURATION; adjust when backend exists.
3) CI: `.github/workflows/ci.yml` runs pre-commit, quality gates via `ci/run_quality_gates.sh` (auto-detects Node/Python projects). Update scripts/tests as code lands.
4) Formatting/linting: see `.editorconfig`, `.prettierrc.json`, and `pyproject.toml` for formatter/linter settings (black/ruff/prettier).

## Structure (see `CODE_MAP.md` for more)
- `docs/`: Design/requirements/test/obs/security/deployment/planning/backlog
- `adr/`: Architecture decisions
- `ci/`: CI helper scripts
- `.github/`: Issue/PR templates and workflows
- `init_codex_project.sh`, `reset_codex_init.sh`: bootstrap helpers

## Next Steps (Stage 4)
- Populate Issues/board with Epics/Features/Tasks from `docs/BACKLOG.md`.
- Add CODE_MAP entries as code is scaffolded; update EPIC_LOG per epic milestones.
- Begin implementation with backend gameplay API (F1/T1–T4), then inference adapter (F2/T5–T6), then frontend loop (F3).

# Contributing Guide

This repo has active backend, frontend, training, and container code. Before changing anything, read `AGENTS.md` for the current Codex operating rules, `docs/README.md` for docs trust order and navigation, and `docs/CURRENT_STATE.md` for the source-verified project snapshot.

## Workflow
- Work through focused branches and PRs when using remote collaboration.
- Inspect `git status --short --branch` before editing.
- Preserve unrelated dirty worktree changes.
- Use `rg --files` and targeted `rg` searches to find source truth.
- Treat older planning docs as historical until verified against code, tests, configs, or recent diffs.
- Use ADRs for material architecture, persistence, infra, cost, or security decisions.

## Quality Gates
- Choose checks based on the files touched and the risk of the change.
- Use backend tests for `app/`, `training/`, `bots/`, `tools/`, and config-affecting changes.
- Use frontend tests/type checks for `frontend/` changes.
- Use smoke or e2e checks for cross-service behavior.
- Avoid coverage drops on touched components without a clear reason in the PR.
- Do not fabricate or bypass test, coverage, security, or readiness results.

## Useful Commands
- `make backend-test`
- `make backend-coverage`
- `make frontend-test`
- `make train-smoke`
- `make smoke`
- `make run`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test:e2e`

## Documentation Expectations
- Update `docs/CURRENT_STATE.md` when a verified repo fact changes.
- Update `CODE_MAP.md` when subsystem boundaries, entrypoints, or command surfaces change.
- Keep README user-facing and concise.
- Keep generated artifacts out of documentation unless the task is specifically about artifacts.

## Generated Files
Do not review, edit, or commit generated outputs unless explicitly requested. Normal navigation should ignore `artifacts/`, `frontend/dist/`, `frontend/dist-training/`, `frontend/coverage/`, caches, local virtualenvs, `git_diag_*`, and `screencaps/`.

## Security And Cost
- Do not commit secrets or local `.env` files.
- Do not introduce paid services, billable infrastructure, or cloud resources without explicit approval.
- Keep logs free of secrets and unnecessary payload dumps.

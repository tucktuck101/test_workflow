# Contributing Guide (Codex Contract v1.4)

## Workflow
- Work via Issues/PRs; use templates in `.github/`.
- Branches: `feature/<desc>`, `fix/<desc>`, `epic/<id>-<desc>`, `proposal/<decision-id>-<desc>` for speculative/high-risk work.
- Apply tag scheme per PROCESS_CHECKLIST (`epic-<id>-start`, `epic-<id>-feature-<name>-done`, `epic-<id>-complete`).
- ADRs required for material decisions (stack, persistence, infra, cost guardrails, architecture shifts). Existing ADRs: 0001–0003.

## Quality Gates (risk: medium, tier: standard)
- Tests: unit + API/contract for start/move/quit; deterministic/stubbed inference tests; coverage targets (engine ≥90%, backend ≥90%, frontend 70–80% with vitest thresholds 75/70/70/75).
- Security: dependency + secrets scanning; SAST/IaC where available.
- Observability: metrics/logs/traces for start/move/quit and inference; update OBSERVABILITY_SPEC when adding operations.
- Coverage guardrail: avoid >2pp drop on affected components without justification in PR.
- Critic Pass required before merge; red-flag human review for auth, data schema/migrations, public API changes, and security-sensitive logic.

## Pre-commit and CI
- Install hooks: `pre-commit install`. Run `pre-commit run -a` before pushing.
- CI: `.github/workflows/ci.yml` runs pre-commit, quality gates (`ci/run_quality_gates.sh`, pytest with 90% gate, vitest with thresholds), and security scans (gitleaks, pip-audit, npm audit).
- Keep CODE_MAP.md updated after structural changes (backend/frontend/training scaffolds).

## Documentation Expectations
- Update docstrings/public API docs for non-trivial modules.
- Keep CODE_MAP.md current after structural changes; update EPIC_LOG.md at epic start/finish.
- Update REQ/ARCH/API/TEST/OBS/SECURITY/DEPLOYMENT docs when behaviour or contracts change.

## Observability & Logging
- Structured logs only; no secrets or payload dumps. Include `game_id`, outcome, model metadata; avoid coordinates/high-cardinality fields and model paths.
- Metrics and traces must cover primary operations; see `docs/OBSERVABILITY_SPEC.md` for required signals.

## Environment/Config
- Use `.env.example` as a template; do not commit secrets. Required envs for runtime: `MODEL_PATH`, `MODEL_VERSION`, `MODEL_HASH`, `MODEL_DEVICE`, `BOARD_SIZE`, `MAX_ACTIVE_GAMES`, `DETERMINISTIC_MODE`, `LOG_LEVEL`, `OBSERVABILITY_ENABLED`. Frontend uses `VITE_API_BASE_URL`.

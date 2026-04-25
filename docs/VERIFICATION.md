# Verification Record

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: rerun after docs, API, runtime, training, frontend, deployment, or command-surface changes.

## Current Truth
This file records compact verification summaries for the active docs suite. It intentionally avoids committing generated logs, screenshots, build outputs, coverage reports, or model artifacts.

## Implemented
| Date | Command or inspection | Result | Notes |
| --- | --- | --- | --- |
| 2026-04-25 | `git status --short --branch` | Completed | Worktree was already dirty before this docs pass; changes were not reverted. |
| 2026-04-25 | `rg --files docs` and targeted `rg` searches | Completed | Identified active docs, historical docs, unresolved task markers, old next-step headings, and old single-layer partial metadata. |
| 2026-04-25 | Source inspection: `app/routes.py`, `app/schemas.py`, `app/health.py`, `app/config.py` | Completed | Verified gameplay, model, training, health/readiness, rate limit, and schema claims used in docs. |
| 2026-04-25 | Source inspection: `app/trainer_orchestrator.py` | Completed | Verified dummy lifecycle behavior and placeholder Compose/Kubernetes adapters. |
| 2026-04-25 | Config inspection: `docker-compose.yml`, `Makefile`, `CODE_MAP.md`, `README.md` | Completed | Verified ports, services, command names, generated path guidance, and source map claims. |
| 2026-04-25 | `make backend-test` | Not run to completion | Failed before tests because `.venv/bin/python` is missing. Fallback `python -m pytest -q` also failed because `pytest` is not installed in the system interpreter. |
| 2026-04-25 | `cd frontend && npm run typecheck` | Passed | TypeScript check completed successfully. |
| 2026-04-25 | `cd frontend && npm run build` | Blocked | Failed before Vite build due missing Rollup optional native package `@rollup/rollup-linux-x64-gnu` in `frontend/node_modules`. |
| 2026-04-25 | `cd frontend && npm run build:training` | Blocked | Failed for the same missing Rollup optional native package. |
| 2026-04-25 | `make train-smoke` | Failed | Training produced a timestamped artifact, then validation failed with `missing_model` while checking `/tmp/.../model.bin`. |
| 2026-04-25 | `./scripts/train_smoke.sh` | Passed | After using `TRAIN_ARTIFACT_NAME` in `training.trainer`, mini training wrote `model.bin`, artifact validation returned `status=ok`, and short eval completed. |
| 2026-04-25 | `make train-smoke` | Passed | Make target now exercises the same passing training, validation, and evaluation smoke path. |
| 2026-04-25 | `make smoke` | Not run | Local runtime stack was not running, and starting Compose was outside this docs-only verification pass. |
| 2026-04-25 | Active-doc stale-text sweep | Passed | No unresolved task markers, old next-step headings, old single-layer partial metadata, stale no-rate-limit language, or stray marker text remained in active docs. |
| 2026-04-25 | Active-doc metadata coverage check | Passed | Every active doc in `docs/README.md`, `docs/CURRENT_STATE.md`, `docs/VERIFICATION.md`, runtime docs, `docs/ml/`, `docs/operations/`, and `docs/portfolio/` has both status metadata lines. |

## Planned
- Re-run focused command checks after installing Python/frontend dependencies.
- Investigate the `make train-smoke` artifact-name mismatch before treating training smoke as passing.
- Run `make smoke` when a local runtime is already available or can be started as part of a demo validation pass.

## Roadmap
- Update this file with pass/fail summaries whenever the focused command checks are rerun.
- Keep evidence terse and link to source docs rather than storing generated artifacts.

## Verification
This verification record was created as part of the active docs refresh on 2026-04-25.

# Case Study: Battleships RL Platform

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: demo path validation, CI/pipeline changes, or orchestration implementation.

## Portfolio Thesis
This project uses Battleships as a controlled environment for demonstrating AI/ML training operations and SRE/Platform Engineering practices. The game rules provide a compact domain for training agents, validating model artifacts, serving inference, and exercising reliability workflows.

## Current Truth
The repository has active backend, frontend, training, container, and test code. Training API orchestration is currently simulated/abstracted; see `docs/ml/TRAINING_ORCHESTRATION.md` for the intended replacement path. Portfolio claims should point to current source or verification summaries.

## What This Demonstrates
- A reproducible ML training domain with scripted opponents, self-play, and evaluation hooks.
- A runtime API that serves game state and agent moves behind health/readiness checks.
- A model artifact lifecycle from training output to validation, promotion, serving, monitoring, and rollback.
- Platform practices around local development, containers, CI, smoke tests, runbooks, and future Kubernetes execution.

## Evidence Map
| Claim | Evidence |
| --- | --- |
| Runtime health/readiness and gameplay flow | `app/routes.py`, `app/health.py`, `scripts/smoke.sh`, `docs/API_SPEC.md` |
| Training/validation flow | `training/`, `tools/validate_artifact.py`, `scripts/train_smoke.sh`, `docs/TRAINER.md` |
| Artifact promotion and rollback practice | `docs/RUNBOOKS.md`, `docs/ml/ARTIFACT_PROMOTION.md` |
| SRE operating model | `docs/operations/SLOS.md`, `docs/operations/ALERTING.md`, `docs/operations/INCIDENT_RESPONSE.md` |
| Honest orchestration status | `docs/ml/TRAINING_ORCHESTRATION.md` |

## Implemented
- Runtime gameplay API, readiness, model metadata, split UIs, smoke scripts, and training code exist.
- Artifact validation and promotion/rollback runbook flow are documented.
- SRE operating model docs cover SLOs, alerting, dashboards, incident response, and RCA examples.

## Planned
- Verified demo run record with command summaries.
- CI evidence snapshot.
- Dashboard and alert artifacts.
- Real process-backed training orchestration.

## Roadmap
- Use `docs/VERIFICATION.md` as the compact evidence record for commands.
- Link screenshots or generated artifacts only if explicitly requested.

## Verification
Reconciled on 2026-04-25 against `docs/CURRENT_STATE.md`, `docs/VERIFICATION.md`, runtime docs, ML docs, and operations docs.

# Demo Path

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: setup, compose, smoke, or training orchestration changes.

## Goal
Show the project as an ML training environment plus SRE/Platform portfolio from a fresh checkout.

## Current Truth
The local demo path exists, but it still depends on valid runtime model artifact configuration. Training API orchestration shown through the UI/API is simulated/abstracted until `app/trainer_orchestrator.py` is replaced with real process-backed execution.

## Implemented
| Capability | Status | Notes |
| --- | --- | --- |
| Local dependency bootstrap (`make setup`) | Implemented | Installs Python and frontend dependencies. |
| Local dev/test parity (`make verify-local`) | Implemented | Runs backend, frontend, and training smoke checks before PR handoff. |
| Training smoke (`make train-smoke`) | Implemented | Produces/validates/evaluates in a temp directory. |
| CI-safe Compose smoke (`make smoke-local`) | Implemented | Uses baked stub model config rather than generated local artifacts. |
| Local stack startup (`make run`) | Partial | Requires model artifact configuration to be valid for readiness. |
| Gameplay/training UIs available on 3000/3001 | Implemented | Through compose frontend containers. |

## Planned
- API-triggered real training orchestration; current API training runs are simulated/abstracted.
- Captured clean-checkout demo evidence with command summaries.

## Repro Steps
1. `make setup`
2. `make verify-local`
3. `make smoke-local`
4. `make run`
5. `curl -sf http://localhost:8000/health/ready`
6. `make smoke`
7. Open `http://localhost:3000` (gameplay UI).
8. Open `http://localhost:3001` (training UI).
9. Confirm readiness/model metadata is visible in gameplay UI.

Expected signals:
- `verify-local` and `train-smoke` complete without errors.
- `smoke-local` starts a CI-safe Compose stack and posts to `/api/games`.
- `/health/ready` returns success before smoke gameplay call.
- `make smoke` successfully posts to `/api/games`.

## Current Caveats
- Generated artifacts are local outputs and are not committed.
- Compose runtime expects configured model artifact values; verify `docker-compose.yml` and current artifact setup before demoing.
- Training API orchestration is currently simulated/abstracted; see `docs/ml/TRAINING_ORCHESTRATION.md`.

## Failure Modes And Recovery
- Readiness fails at startup:
  verify model path/hash/device config in compose settings and active artifact files.
- Smoke fails while readiness passes:
  check backend logs and route-level errors for `/api/games`.
- Training UI works but run results look synthetic:
  this is expected until real process-backed orchestration is implemented.

## Roadmap
- Promote the demo capability status only after one clean-checkout validation run is captured with command output summaries.
- Keep this doc linked to `docs/ml/TRAINING_ORCHESTRATION.md` so demo viewers understand the orchestration boundary.

## Verification
Reconciled on 2026-04-25 against `Makefile`, `docker-compose.yml`, `README.md`, `app/trainer_orchestrator.py`, and `docs/VERIFICATION.md`.

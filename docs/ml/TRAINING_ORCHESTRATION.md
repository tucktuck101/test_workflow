# Training Orchestration

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: trainer orchestration backend/UI/API behavior changes.

## Current Truth
The API exposes training run lifecycle endpoints, but the current orchestrator path simulates or abstracts execution rather than launching a real local, Compose, or Kubernetes training job. `DummyTrainerOrchestrator` uses in-memory state and a timer. Compose and Kubernetes orchestrators are placeholders that delegate to dummy behavior. Do not present this as production training orchestration yet.

## Implemented
| Capability | Status | Notes |
| --- | --- | --- |
| `/api/training/runs` lifecycle API shape | Implemented | Start/status/cancel/metrics endpoints exist. |
| In-memory run state transitions | Implemented | Pending/running/succeeded/failed/canceled transitions are modeled. |

## Planned
| Capability | Status | Notes |
| --- | --- | --- |
| Real local process execution for training runs | Planned | Not yet wired through trainer orchestrator. |
| Compose-backed trainer job execution | Planned | Placeholder path only. |
| Kubernetes job execution via API | Planned | Placeholder path only. |

## Target Local Implementation
Replace simulated runs with a process-backed local orchestrator that can:

- Start a training process with a generated run ID.
- Write run output to a run-specific artifact directory.
- Capture status, timestamps, errors, and basic metrics.
- Surface logs or log paths.
- Cancel a running process.
- Keep the API response shape stable where possible.

Minimum acceptance criteria for this upgrade:
- training run starts an actual process and transitions to terminal states from process outcome.
- API exposes enough run detail for UI/operator triage.
- cancellation stops process and marks run canceled.
- artifact output path is deterministic and documented.
- tests cover start/status/cancel/failure.

## Later Platform Targets
- Compose-backed trainer service execution.
- Kubernetes Job creation for isolated training workloads.
- Artifact handoff from training job to validation/promotion flow.

## Roadmap
- Implement a local subprocess-backed orchestrator first.
- Keep the API response shape stable where possible.
- Evaluate Compose and Kubernetes adapters as separate milestones after local process execution is real.

## Verification
Reconciled on 2026-04-25 against `app/trainer_orchestrator.py`, `app/routes.py`, `app/schemas.py`, `frontend/src/TrainingControl.tsx`, and `docker-compose.yml`.

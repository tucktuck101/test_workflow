# Dashboards

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: metric name/schema updates or alert rule rollout.

## Purpose
Define dashboard panels that would make the ML training and runtime system observable.

## Current Truth
Dashboard panel candidates are documented. Stored dashboard JSON, screenshots, or concrete telemetry-backed dashboard artifacts are not yet committed.

## Candidate Panels
- Model readiness status with active version/hash.
- Gameplay API request rate, errors, and latency.
- Inference latency and error rate.
- Active games and completions by outcome.
- Training job status, duration, and success/failure counts.
- Artifact validation outcomes.
- Container resource usage for backend and trainer.

## Implemented
| Dashboard Surface | Status | Notes |
| --- | --- | --- |
| Runtime panel definitions | Partial | Candidate panel set exists, implementation artifacts pending. |
| Training pipeline panel definitions | Partial | Candidate panel set exists, depends on real orchestration signals. |
| Stored dashboard artifacts (JSON/screenshots) | Planned | Not yet committed. |

## Minimum Dashboard Set
- Runtime board:
  readiness, API latency/error, inference latency/error, active games.
- Training board:
  run state counts, duration, failures, artifact validation outcomes.
- CI board:
  smoke pass rate and training smoke pass rate over time.

## Planned
- Baseline dashboard examples as JSON or screenshots once instrumentation signals are stable.
- Training pipeline panels after real orchestration emits reliable signals.
- Portfolio links to dashboard evidence.

## Roadmap
- Keep candidate panels aligned with `docs/OBSERVABILITY_SPEC.md`.
- Do not commit generated screenshots or dashboard exports unless explicitly requested.

## Verification
Reconciled on 2026-04-25 against observability docs, SLO docs, alerting docs, and current orchestration status.

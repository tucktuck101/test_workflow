# SLOs And SLIs

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: observability metrics names, CI smoke behavior, or runtime/training orchestration changes.

## Purpose
Define reliability targets for the training and inference system. These are portfolio-oriented draft SLOs until measured baselines exist.

## Current Truth
Health/readiness endpoints and smoke commands exist. Production-grade SLI collection, dashboard evidence, and formal SLO gates are still partial/planned.

## Implemented
| Capability | Status | Notes |
| --- | --- | --- |
| Health/readiness endpoints available | Implemented | Readiness is tied to model load state. |
| Smoke checks for runtime and training paths | Implemented | `make smoke` and `make train-smoke`. |
| Production-grade SLI telemetry pipeline | Partial | Docs and placeholders exist; dashboards/alerts still maturing. |
| Formal SLO policy enforcement | Planned | Targets documented but not automated as policy gates. |

## Candidate SLIs
- Training job success rate.
- Artifact validation success rate.
- Model readiness success rate.
- Inference/API move request success rate.
- Inference latency p95.
- Smoke-test success rate.
- Rollback completion time after bad artifact promotion.

## Draft SLO Targets
- Model readiness succeeds for 99.9% of runtime checks in demo/prod-like operation.
- Validated artifacts pass promotion checks before runtime configuration changes.
- Gameplay move API returns successful responses for 99% of valid requests in demo load tests.
- Training smoke succeeds on every protected-branch CI run.

## Measurement Windows
- Local demo: per run/session validation.
- CI: per workflow run and rolling 7-day view.
- Prod-like environments: 5-minute and 30-day windows.

## Planned
- Measured baselines from CI, local smoke, and local load runs.
- Alert mappings with stable rule IDs and owners.
- Formal policy gates once thresholds are trustworthy.

## Roadmap
- Record measured baselines in `docs/VERIFICATION.md` or a linked evidence note.
- Replace draft targets only after observed thresholds exist.

## Verification
Reconciled on 2026-04-25 against `Makefile`, health/readiness source, observability docs, alerting docs, and dashboard docs.

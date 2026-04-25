# Alerting

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: metrics naming, runbook changes, or SLO target updates.

## Purpose
Describe alert conditions that matter for operating the training and inference system.

## Current Truth
Alert conditions and severity mapping are documented, but concrete alert rule implementations, owners, and rule IDs are not yet committed.

## Candidate Alerts
- Model readiness failing for more than 2 minutes.
- Artifact validation failure during promotion.
- Training smoke failure in CI.
- Inference error rate above threshold.
- Move API p95 latency above threshold.
- Active games near configured capacity.
- Training run stuck in pending/running state beyond expected duration.

## Implemented
| Alert Area | Status | Notes |
| --- | --- | --- |
| Readiness failure detection | Partial | Endpoint + runbook guidance exists; alert automation not finalized. |
| Artifact promotion validation failure | Partial | Validation CLI and runbook exist; central alerting policy pending. |
| API latency/error alerts | Planned | Thresholds documented; rule implementations pending. |
| Training orchestration stuck-run alerts | Planned | Depends on real orchestration implementation. |

## Initial Severity Mapping
- `P1`: readiness failing >2 minutes in active environment.
- `P1`: post-promotion inference error spike above agreed threshold.
- `P2`: training smoke failure on protected branch CI.
- `P3`: capacity nearing configured max active games.

## Runbook Mapping
- Promotion/rollback alerts:
  `docs/RUNBOOKS.md`
- Incident handling flow:
  `docs/operations/INCIDENT_RESPONSE.md`
- Example RCA template:
  `docs/operations/RCA_EXAMPLE.md`

## Planned
- Concrete alert rules once metric names and exporters are stabilized.
- Rule IDs, owners, and runbook URLs.
- Stuck-run alerts after real training orchestration exists.

## Roadmap
- Keep alert conditions synchronized with `docs/operations/SLOS.md` and `docs/OBSERVABILITY_SPEC.md`.
- Add concrete rule IDs only when actual rule artifacts exist.

## Verification
Reconciled on 2026-04-25 against observability docs, SLO docs, runbooks, and training orchestration status.

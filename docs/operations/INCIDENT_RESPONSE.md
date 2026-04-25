# Incident Response

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: runbook changes, alert taxonomy changes, or training orchestration implementation.

## Purpose
Define the response shape for failures in model training, artifact promotion, and runtime inference.

## Current Truth
The response model and minimal local commands are documented. Environment-specific Compose and future Kubernetes incident commands are pending.

## Incident Types
- Bad artifact promoted and readiness fails.
- Artifact passes readiness but inference error rate increases.
- Training job fails or stalls.
- Smoke tests fail after infrastructure or config change.
- Runtime reaches active game capacity.

## Response Pattern
1. Confirm impact and current version/config.
2. Check readiness, logs, metrics, and latest CI/smoke results.
3. Roll back artifact or config if runtime is impaired.
4. Preserve failing artifact/config for investigation.
5. Record timeline, root cause, fix, and follow-up work.

## Minimal Command Set
- Check readiness:
  `curl -sf http://localhost:8000/health/ready`
- Smoke runtime quickly:
  `make smoke`
- Validate candidate artifact:
  `python -m tools.validate_artifact --artifact <path> --manifest <path> --root <root> --device <cpu|cuda>`
- Roll back model config:
  apply previous `MODEL_PATH`, `MODEL_VERSION`, `MODEL_HASH`, `MODEL_DEVICE` values and restart backend/runtime.

## Ownership And Escalation
- Incident commander:
  on-call maintainer for this repo.
- Escalation path:
  if runtime impaired and rollback fails, pause promotions and open incident tracking issue immediately.

## Runbook Links
- Promotion and rollback:
  `docs/RUNBOOKS.md`
- RCA template/example:
  `docs/operations/RCA_EXAMPLE.md`

## Implemented
- Incident types and response pattern for artifact, inference, training, smoke, and capacity failures.
- Minimal local command set for readiness, smoke, artifact validation, and rollback config.
- Links to promotion/rollback runbooks and RCA example.

## Planned
- Compose-specific command variants.
- Kubernetes-specific command variants after deployment/orchestration paths are finalized.
- Alert IDs and dashboard links when concrete artifacts exist.

## Roadmap
- Keep this file synchronized with `docs/RUNBOOKS.md`, `docs/operations/ALERTING.md`, and `docs/operations/RCA_EXAMPLE.md`.
- Add environment-specific commands only after those paths are verified.

## Verification
Reconciled on 2026-04-25 against runbooks, alerting docs, Docker Compose, and training orchestration status.

# RCA Example: Bad Model Artifact Fails Readiness

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: real incident evidence, promotion flow, validation flow, or readiness behavior changes.

## Current Truth
This is a synthetic RCA example for portfolio and operating-model purposes. Replace or supplement it only after a real project incident exists.

## Summary
A newly promoted model artifact fails backend readiness because the configured hash does not match the artifact on disk.

## Impact
Runtime traffic should not be served by the new artifact. Readiness blocks the backend from becoming healthy with the bad configuration.

## Timeline
- T0: Candidate artifact is selected for promotion.
- T1: Runtime config is updated with candidate path/version/hash.
- T2: `/health/ready` returns not ready due to hash mismatch.
- T3: Operator rolls back to previous artifact configuration.
- T4: Follow-up issue is opened to fix promotion validation.

## Root Cause
The artifact and manifest/config values were not validated together immediately before promotion.

## Corrective Actions
- Require `tools.validate_artifact` before promotion.
- Store previous artifact manifest for rollback.
- Add CI/manual workflow evidence to promotion notes.

## Implemented
- Example impact, timeline, root cause, and corrective actions for readiness failure after bad artifact promotion.
- Links conceptually to validation, rollback, and incident response docs.

## Planned
- Real project incident example once one exists.
- Exact commands and log examples from an implemented promotion flow.

## Roadmap
- Keep this as synthetic until real evidence exists.
- Link future real incident evidence from `docs/operations/INCIDENT_RESPONSE.md` and portfolio docs.

## Verification
Reconciled on 2026-04-25 against readiness behavior, validation docs, runbooks, and incident-response docs.

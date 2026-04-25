# Model Lifecycle

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: training output, manifest, validation, promotion, serving, or rollback behavior changes.

## Current Truth
Training, validation, and runtime loading paths exist, but the full artifact lifecycle is not yet standardized end to end. Promotion remains documented as an operator flow rather than a single automated pipeline.

## Intended Lifecycle
1. Generate model artifact through training.
2. Write manifest with version, hash, device, seed/config metadata, and timestamp.
3. Validate artifact and manifest before promotion.
4. Promote artifact by updating runtime configuration.
5. Serve artifact through the backend agent adapter.
6. Monitor readiness, inference latency, errors, and gameplay outcomes.
7. Roll back to the previous known-good artifact when readiness or quality regresses.

## Current State
Training, validation, and runtime loading paths exist, but the full lifecycle is not yet standardized end to end.

## Implemented
- Training code can emit artifacts and metadata through local training paths.
- Runtime readiness checks model path, version, hash, device, and file integrity.
- Artifact validation tooling exists in `tools/validate_artifact.py`.
- Promotion and rollback procedures are documented in `docs/RUNBOOKS.md`.

## Planned
- Canonical artifact naming.
- Manifest schema ownership and compatibility rules.
- Promotion evidence examples.
- Rollback test or smoke path.

## Roadmap
- Standardize artifact naming and manifest compatibility before promoting the capability status.
- Link accepted/rejected evaluation examples from `docs/ml/EVALUATION_STRATEGY.md` once thresholds exist.

## Verification
Reconciled on 2026-04-25 against training directories, `tools/validate_artifact.py`, runtime readiness source, and runbook docs.

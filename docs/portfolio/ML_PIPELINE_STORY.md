# ML Pipeline Story

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: training, evaluation, artifact validation, promotion, or serving behavior changes.

## Narrative
The project trains Battleships agents in a controlled environment, validates generated model artifacts, and serves selected artifacts through the gameplay API.

## Current Truth
Training modules, configs, validation tooling, and smoke paths exist. Artifact naming, manifest compatibility rules, promotion thresholds, and verified promotion examples remain planned.

## Intended Flow
1. Configure training through YAML and/or the training UI.
2. Train with scripted opponents, self-play, or DQN paths.
3. Emit a model artifact plus manifest metadata.
4. Validate artifact path, hash, device, and manifest consistency.
5. Promote a validated artifact into runtime configuration.
6. Serve agent moves through the backend adapter.
7. Monitor readiness, inference latency, errors, and gameplay outcomes.
8. Roll back to the previous artifact if readiness or inference quality regresses.

## Current Evidence
- Training modules live in `training/`.
- Training configs live in `configs/`.
- Validation CLI lives in `tools/validate_artifact.py`.
- Training smoke path lives in `scripts/train_smoke.sh`.

## Implemented
- Training, curriculum, DQN/self-play, evaluation, and validation code paths exist.
- Runtime serving reads configured model artifact metadata and readiness state.
- Training smoke command surface exists through `make train-smoke`.

## Planned
- Standardized artifact naming and manifest schema.
- Verified promotion example.
- Baseline evaluation metrics for at least one artifact.
- Accepted/rejected artifact portfolio examples.

## Roadmap
- Keep lifecycle details synchronized with `docs/ml/MODEL_LIFECYCLE.md`, `docs/ml/EVALUATION_STRATEGY.md`, and `docs/ml/ARTIFACT_PROMOTION.md`.
- Promote capability status only after a verified artifact moves through evaluation, validation, promotion, readiness, and rollback evidence.

## Verification
Reconciled on 2026-04-25 against `training/`, `configs/`, `tools/validate_artifact.py`, `scripts/train_smoke.sh`, and ML lifecycle docs.

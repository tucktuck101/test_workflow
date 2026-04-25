# Evaluation Strategy

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: evaluation code, training smoke, model thresholds, or promotion-gate changes.

## Purpose
Define how trained Battleships agents are judged before promotion.

## Current Truth
Evaluation code and training smoke checks exist, but promotion-quality thresholds are not yet formalized.

## Candidate Evaluation Signals
- Win rate against scripted opponents.
- Move efficiency.
- Baseline comparison against previous artifact.
- Inference latency and error behavior.
- Determinism/reproducibility for seeded runs.

## Implemented
- Training/evaluation modules exist under `training/`.
- `make train-smoke` runs a small training, validation, and evaluation flow through `scripts/train_smoke.sh`.
- Artifact validation can be used before promotion.

## Planned
- Minimum promotion thresholds.
- Baseline comparison output against previous artifacts.
- Evaluation results recorded in the artifact manifest or companion report.
- Small portfolio example of an accepted and rejected artifact.

## Roadmap
- Define thresholds only after baseline command summaries are captured.
- Link accepted/rejected examples into `docs/portfolio/ML_PIPELINE_STORY.md`.

## Verification
Reconciled on 2026-04-25 against training directories, `scripts/train_smoke.sh`, `Makefile`, and model lifecycle docs.

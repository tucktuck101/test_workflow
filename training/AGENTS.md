# Training Agent Guide

## Purpose
Use this guide for changes under `training/`. The root `AGENTS.md` still applies; this file covers offline training, evaluation, curriculum, and artifact-producing code.

## Local Source Truth
- `trainer.py` is the classic artifact-producing trainer path.
- `dqn_selfplay.py`, `dqn_trainer.py`, `selfplay_trainer.py`, `env.py`, `vectorized_env.py`, `state_encoder.py`, and `policy.py` cover DQN/self-play training behavior.
- `curriculum.py` owns curriculum state and phase progression.
- `config.py` and `config_loader.py` own training config dataclasses, YAML loading, schema validation, and value checks.
- `eval.py` evaluates artifacts.
- Related source lives outside this directory: `configs/`, `scripts/train_smoke.sh`, `tools/validate_artifact.py`, and `bots/scripted_opponents.py`.

## Editing Guidance
- Keep YAML config files and schemas in `configs/` aligned with dataclass fields and loader validation.
- Keep training behavior deterministic where seeds already exist; tests and smoke flows depend on reproducible small runs.
- Treat model quality and promotion readiness as unproven unless validated by evaluation and artifact checks.
- Keep generated models, metrics, plots, manifests, and local experiment outputs out of reviews unless the task explicitly asks for them.
- Check bot policy changes against both gameplay and training use cases when scripted opponents are involved.

## Focused Checks
- Config or curriculum changes: targeted `pytest tests/test_curriculum.py tests/test_config.py`.
- Training flow changes: targeted `pytest tests/test_training.py`.
- Bot-related training behavior: targeted `pytest tests/test_scripted_opponents.py`.
- Artifact handoff changes: run the relevant `tools.validate_artifact` command or `make train-smoke` when practical.
- Broad training behavior changes: `make train-smoke` is the preferred end-to-end smoke.

## Docs Triggers
- Update `docs/ml/*` when lifecycle, orchestration, evaluation, or artifact promotion behavior changes.
- Update `docs/CURRENT_STATE.md` only when a verified training capability changes.
- Update `CODE_MAP.md` when training entrypoints, configs, or command surfaces change.

## Pitfalls
- Do not present API training runs as real training execution from this directory unless backend orchestration is also changed.
- Do not assume an artifact is production-ready because a file exists.
- Do not hand-edit generated metrics or artifacts to satisfy tests or docs.

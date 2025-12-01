# Curriculum Configuration

The DQN self-play runner now loads a curriculum that describes which opponents and hyperparameters to use per phase.

- Schema lives at `configs/curriculum.schema.yaml`.
- Default configuration is `configs/curriculum.default.yaml` and is automatically loaded when no custom path is provided.
- The runner accepts `--curriculum <path>` or a `curriculum:` section in the YAML passed to `--config`.

## Schema overview

- `version`: schema version string.
- `phases[]`: ordered list of phases.
  - `id`, `name`, `description`: identifiers and description.
  - `gating`: gates for advancing (`min_episodes`, `min_rounds`, `min_win_rate`, `min_avg_moves`, `min_baseline_win_rate`).
  - `opponents[]`: opponent mix with `opponent` (type) and positive `weight` plus optional `params`.
  - `hyperparams`:
    - `train`: overrides for board sizing, adjacency, ships, and reward shaping knobs.
    - `dqn`: overrides for epsilon schedule, lr, gamma, buffer/batch sizes, target updates, etc.
    - `selfplay`: overrides for chunking, thresholds, workers, gates.

## Usage

```
python -m training.dqn_selfplay --config configs/dqn_train.yaml \
  --curriculum configs/curriculum.custom.yaml
```

Invalid curriculum files fail fast with a clear error message before training starts.

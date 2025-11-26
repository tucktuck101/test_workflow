# Data Model (MVP)

## Game Session (in-memory)
- `game_id` (UUID): session key.
- `player_board` (10x10 grid): ships placed; cell states: `unknown | miss | hit | sunk`.
- `agent_board_masked` (10x10 grid): client-facing mask without revealing ships; tracks outcomes.
- `agent_board_full` (server-only): full placement used for adjudication.
- `ships`: list of ships with `name`, `size`, `coordinates[]`, `hits[]`, `status: afloat|sunk`.
- `move_history`: ordered list of moves:
  - `actor: player|agent`
  - `x`, `y`
  - `outcome: hit|miss|sunk|invalid`
  - `timestamp`
- `status`: `in_progress | player_won | agent_won | quit | aborted`.
- `created_at`, `updated_at`, `ended_at`.
- `deterministic_seed` (optional): used for tests/repro and agent stub.

## Errors/Validation States
- `invalid_coordinates`, `duplicate_move`, `game_not_found`, `game_finished`, `inference_unavailable`.

## Model Artifact Metadata
- `MODEL_VERSION`: semantic or timestamped version string.
- `MODEL_PATH`: absolute/volume-mounted path to artifact.
- `MODEL_HASH`: SHA256 of artifact for integrity check.
- `DEVICE`: `cpu|cuda` selected at startup.
- `loaded_at`: timestamp; `load_status: loaded|failed`.

## Training Outputs
- Artifact file(s) (weights, config).
- Training run metadata: hyperparameters, seed, date, dataset reference; stored with artifact for audit (out of scope for runtime but noted for promotion).

## Future Persistence (post-MVP)
- Relational store (e.g., Postgres) for game history, users, leaderboards; introduces tables for `users`, `games`, `moves`, `artifacts`.

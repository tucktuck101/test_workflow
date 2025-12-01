# Configuration

## Environment Variables
- `API_PORT` (default: 8000): Backend listen port.
- `API_HOST` (default: 0.0.0.0): Bind host.
- `FRONTEND_ORIGIN` (optional): Allowed origin(s) for CORS.
- `MODEL_PATH` (required): Filesystem path to the model artifact.
- `MODEL_ROOT` (optional): Allowed root directory for model artifacts (default: parent directory of `MODEL_PATH`); `MODEL_PATH` must reside within this root.
- `MODEL_VERSION` (required): Version string for the loaded model.
- `MODEL_HASH` (required): SHA256 to verify model integrity.
- `MODEL_DEVICE` (default: cpu): `cpu` or `cuda` if available.
- `BOARD_SIZE` (default: 10): Board dimension for validation.
- `LOG_LEVEL` (default: info): Logging verbosity.
- `OBSERVABILITY_ENABLED` (default: true): Toggle metrics/tracing emission.
- `DETERMINISTIC_MODE` (default: false): If true, seed/stub inference for tests/local dev.
- `MAX_ACTIVE_GAMES` (default: 100): Soft cap for concurrent in-memory sessions.
- Reward shaping (training): `REWARD_STEP_BASE` (default -0.05), `REWARD_STEP_DECAY` (0), `REWARD_STEP_CAP` (-0.5), `REWARD_HIT` (1.0), `REWARD_MISS` (0.0), `REWARD_SINK_MULT` (1.0), `REWARD_WIN_MAX` (5.0), `REWARD_WIN_DECAY_K` (82.0), `REWARD_PERFECT_MOVE` (17), `REWARD_LOSS` (-10.0); self-play promotion gate on average moves via `DQN_MOVE_GATE` (optional).

## Files and Paths
- `.env` for local development; never commit secrets.
- Model artifacts stored under a dedicated directory or mounted volume; path validated to avoid traversal outside allowed root.
- A ready-to-use stub model artifact is provided at `models/stub_model.bin` with:
  - `MODEL_HASH=9d282bb3026000b1535a0129145ad46fba61fab5799be1a65928797e61d3006e`
  - `MODEL_VERSION=stub-v1`
  - `MODEL_PATH=./models/stub_model.bin`
  Use this for dev/CI readiness and deterministic inference.

## Defaults and Overrides
- Local dev may set `.env` using `.env.example` as template.
- Kubernetes deployments should use ConfigMaps for non-secret values and Secrets for any sensitive data introduced later (none expected in MVP).

## Failure Handling
- On startup, backend verifies `MODEL_PATH` exists and `MODEL_HASH` matches; readiness fails if verification or load fails.
- Missing required envs should fail fast at startup.

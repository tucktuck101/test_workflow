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
- `MAX_ACTIVE_GAMES` (optional): Soft cap for concurrent in-memory sessions.

## Files and Paths
- `.env` for local development; never commit secrets.
- Model artifacts stored under a dedicated directory or mounted volume; path validated to avoid traversal outside allowed root.

## Defaults and Overrides
- Local dev may set `.env` using `.env.example` as template.
- Kubernetes deployments should use ConfigMaps for non-secret values and Secrets for any sensitive data introduced later (none expected in MVP).

## Failure Handling
- On startup, backend verifies `MODEL_PATH` exists and `MODEL_HASH` matches; readiness fails if verification or load fails.
- Missing required envs should fail fast at startup.

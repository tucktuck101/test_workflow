# CODE_MAP (to be updated as code is added)

## Repository Layout
- `README.md`: project overview and workflow.
- `CONTRIBUTING.md`: contribution and Quality Gate expectations.
- `PROCESS_CHECKLIST.md`: governance workflow guide.
- `PROJECT_POLICY.yaml`: profile/tier/repo strategy/security guardrails.
- `docs/`: design and planning docs (VISION, REQUIREMENTS, USER_STORIES, ARCHITECTURE, DATA_MODEL, API_SPEC, TEST_STRATEGY, OBSERVABILITY_SPEC, SECURITY_NOTES, DEPLOYMENT, RUNBOOKS, BACKLOG, STAGE4_PLANNING, EPIC_LOG).
- `adr/`: architecture decisions (0001 workflow/tier, 0002 tech stack/runtime, 0003 state/model handling).
- `.github/`: Issue/PR templates, CI workflow.
- `ci/`: quality gates script.
- `.env.example`, `CONFIGURATION.md`: environment/config guidance.
- `models/stub_model.bin`: lightweight stub artifact for dev/CI (hash `9d282bb3026000b1535a0129145ad46fba61fab5799be1a65928797e61d3006e`, version `stub-v1`).
- `init_codex_project.sh`, `reset_codex_init.sh`: bootstrap helpers.
- `.editorconfig`, `.prettierrc.json`, `.pre-commit-config.yaml`, `pyproject.toml`: formatting/linting config for Python/JS and pre-commit.

## Current Code Structure
- `app/`: FastAPI scaffold and configuration.
  - `config.py`: environment/config parsing and validation (paths, devices, limits).
  - `main.py`: FastAPI app factory and uvicorn runner.
  - `engine.py`: game session model, ship placement (deterministic-capable), move adjudication, in-memory session store.
  - `agent.py`: deterministic-capable agent stub.
  - `errors.py`: structured error helpers.
  - `health.py`: readiness hash/path checks.
  - `rate_limit.py`: simple token bucket guard.
  - `routes.py`: gameplay routes and health endpoints; readiness/rate limiting.
  - `model_loader.py`: model hash/path readiness validation.
  - `obs.py`: observability scaffold (spans/metrics placeholders).
- `tests/`: Python tests.
  - `test_config.py`: settings/env validation and app smoke test.
  - `test_engine.py`: game engine/session tests (determinism, validation, outcomes).
  - `test_health.py`: health/readiness tests.
  - `test_rate_limit.py`: rate-limit guard tests.
  - `test_agent.py`: deterministic agent tests.
  - `test_routes.py`: gameplay API happy/error/capacity/idempotent and inference-failure cases.
  - `test_session_store.py`: session store TTL/end behavior.
  - `test_main.py`: CORS middleware behavior and preflight checks.
- `requirements.txt`: Python dependencies (fastapi, uvicorn, pytest, mypy, otel).
- `Makefile`: common tasks (backend coverage/typecheck, frontend tests, load test stub).
- `frontend/`: React/Vite SPA for gameplay loop.
  - `src/App.tsx`: UI for start/move/quit, boards, readiness badge, error/backoff messaging.
  - `src/api.ts`: client wrapper, error mapping, config handling for `VITE_API_BASE_URL`.
  - `src/styles.css`: design tokens/layout.
  - `src/types.ts`: shared frontend types.
  - `src/App.test.tsx`, `src/api.test.ts`: RTL/vitest coverage for flows and error mapping.
  - `vite.config.ts`, `vitest.config.ts`, `tsconfig.json`, `package.json`, `package-lock.json`.
- `docker-compose.yml`: local backend/frontend composition; healthcheck wiring.
- `Dockerfile.backend`: backend container (FastAPI).
- `Dockerfile.frontend`: builds Vite frontend into nginx.
- `load_tests/k6_load.js`: k6 load test stub for start/move endpoints.
- `load_tests/README.md`: how/when to run k6 load stub and target baselines.
- `pytest.ini`: test warning filters.
- `.devcontainer/`: VS Code devcontainer for Python 3.11 + Node 20 setup.
- `training/`: stub training pipeline.
  - `config.py`: training config/env parsing.
  - `env.py`: Battleship training environment with rewards/actions.
  - `policy.py`: simple Q-learning policy.
  - `trainer.py`: trains policy and emits artifact + manifest (hash/version/device/episodes/hparams).
  - `eval.py`: evaluate trained policy.
  - `tests/test_training.py`: verifies deterministic artifact/manifest, validator, env rewards, and eval.
  - `tools/validate_artifact.py`: CLI to validate artifact vs manifest/hash/root/device for promotion checks.
- `.github/workflows/artifact-validate.yml`: manual workflow to run artifact validation CLI for promotions.
- `app/rate_limit.py`: token bucket limiter with RateLimitExceeded.
- `tests/test_rate_limit.py`: ensures 429 with Retry-After and non-limited path.

## Planned Additions
- Frontend: React/Vite app, components, API client, tests.
- Training: RL training pipeline scripts and artifacts.

Update this map when scaffolding code and new modules are added.***

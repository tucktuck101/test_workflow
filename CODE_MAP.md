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
- `init_codex_project.sh`, `reset_codex_init.sh`: bootstrap helpers.
- `.editorconfig`, `.prettierrc.json`, `.pre-commit-config.yaml`, `pyproject.toml`: formatting/linting config for Python/JS and pre-commit.

## Current Code Structure
- `app/`: FastAPI scaffold and configuration.
  - `config.py`: environment/config parsing and validation (paths, devices, limits).
  - `main.py`: FastAPI app factory and uvicorn runner.
- `app/engine.py`: game session model, ship placement (deterministic-capable), move adjudication, in-memory session store.
- `tests/`: Python tests.
  - `test_config.py`: settings/env validation and app smoke test.
  - `test_engine.py`: game engine/session tests (determinism, validation, outcomes).
- `requirements.txt`: Python dependencies (fastapi, uvicorn, pytest).

## Planned Additions
- Backend gameplay modules: game engine, session store, agent adapter, API routes.
- Frontend: React/Vite app, components, API client, tests.
- Training: RL training pipeline scripts and artifacts.

Update this map when scaffolding code and new modules are added.***

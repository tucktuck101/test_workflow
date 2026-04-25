# Code Map

This is a compact source-oriented map for navigation. It is not a backlog and should not be used as proof that a feature is complete. Verify behavior against source and tests.

## First Reads
- `AGENTS.md`: Codex operating guide and source-of-truth rules.
- `docs/CURRENT_STATE.md`: current implementation snapshot.
- `README.md`: human-facing overview and common commands.
- `PROJECT_POLICY.yaml`: project constraints such as local-only cost guardrails and allowed stack.
- `docs/portfolio/CASE_STUDY.md`: portfolio framing for the ML training and SRE/platform story.
- `docs/DEMO_PATH.md`: intended fresh-checkout demo path and caveats.

## Backend
- `app/main.py`: FastAPI app factory and runtime wiring.
- `app/routes.py`: gameplay, model, training, and health route registration.
- `app/schemas.py`: API request/response models.
- `app/engine.py`: Battleship rules, sessions, ship placement, moves, and in-memory session store.
- `app/agent.py`: deterministic, policy, and `.npz` agent move adapter paths.
- `app/model_loader.py` and `app/health.py`: model readiness and health payload support.
- `app/rate_limit.py`: simple rate limiting.
- `app/trainer_orchestrator.py`: training run lifecycle abstraction; verify implementation before assuming real job orchestration.

## Frontend
- `frontend/src/App.tsx`: gameplay UI.
- `frontend/src/TrainingControl.tsx`: training control UI.
- `frontend/src/api.ts`: browser API client and error mapping.
- `frontend/src/types.ts`: frontend API and UI types.
- `frontend/src/styles.css`: shared styling.
- `frontend/src/main.tsx` and `frontend/src/training.tsx`: Vite entrypoints.
- `frontend/vite.config.ts` and `frontend/vite.training.config.ts`: gameplay and training UI builds.

## Training And Bots
- `training/`: training configs, envs, policies, state encoding, vectorized envs, DQN/self-play, curriculum, trainer, and eval code.
- `configs/`: YAML configs and schemas for DQN training and curriculum.
- `bots/scripted_opponents.py`: scripted opponents used by gameplay/training paths.
- `tools/validate_artifact.py`: artifact validation CLI.
- `scripts/train_smoke.sh`: small training validation flow.
- `scripts/verify_local.sh`: local dev/test parity check before PR handoff.
- `scripts/smoke_local.sh`: CI-safe Compose smoke path.
- `scripts/plot_dqn_metrics.py`: metrics plotting helper.

## Containers And Deployment
- `docker-compose.yml`: local backend, gameplay frontend, training UI, and trainer services.
- `docker-compose.ci.yml`: CI-safe runtime smoke stack with baked model defaults.
- `Dockerfile.backend`: backend image.
- `Dockerfile.frontend`: gameplay frontend image.
- `Dockerfile.training-frontend`: training UI image.
- `Dockerfile.trainer`: trainer image.
- `k8s/base/` and `k8s/overlays/k3s/`: runtime deployment/service manifests.
- `k8s/trainer-job.yaml` and `k8s/trainer-cronjob.yaml`: trainer workload manifests.

## Tests
- `tests/`: backend, game engine, route, training, session, config, health, and bot tests.
- `frontend/src/*.test.tsx` and `frontend/src/*.test.ts`: Vitest/RTL frontend tests.
- `frontend/e2e/`: Playwright e2e tests.
- `load_tests/`: k6 load-test stub and notes.

## Portfolio And Operations Docs
- `docs/portfolio/`: case study, architecture overview, ML pipeline story, and SRE/platform story.
- `docs/operations/`: SLO, alerting, dashboard, incident response, and RCA stubs.
- `docs/ml/`: model lifecycle, artifact promotion, training orchestration, and evaluation strategy.
- `docs/history/`: historical planning and governance docs preserved for context.

## Generated Or Local-Only
Normally ignore `artifacts/`, `frontend/dist/`, `frontend/dist-training/`, `frontend/coverage/`, `.coverage`, caches, `.venv/`, `frontend/node_modules/`, `git_diag_*`, and `screencaps/`.

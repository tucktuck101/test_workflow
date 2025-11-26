# Deployment (Plan)

## Local (MVP)
- Backend: Python/FastAPI app; run locally with uvicorn; loads static RL model artifact from local path.
- Frontend: React/TypeScript dev server (Vite or similar); points to local API.
- Config: environment variables for model path, feature toggles, ports, device selection; no secrets committed.
- Health: use `/health/live` and `/health/ready` for basic checks; readiness tied to model load.

## Containerization
- Build separate images for backend and frontend; include model artifact via volume/mount or image layer for runtime.
- GPU support for training/inference images where available; default to CPU otherwise; make device configurable via env.
- Backend image should verify model hash at startup and fail if mismatch.
- Expose health endpoints; wire readiness/liveness probes in container configs.

## Kubernetes Readiness
- Namespaces for dev/test/prod; training runs in separate namespace/environment.
- Manifests/Helm overlays later: deployments, services, configmaps/secrets, readiness/liveness probes using health endpoints.
- Storage for model artifact (e.g., mounted volume or config-backed object) when running in k8s.
- Configure resource requests/limits for backend (CPU/GPU) and training jobs; include node selectors/tolerations for GPU if used.

## Environments
- dev/test/prod for runtime; training isolated. Local-first until cloud deployment is approved (no paid services during MVP).
- Model promotion flow: training outputs artifact + metadata; promoted by copying into runtime artifact bucket/volume with version/hash recorded in config.

## Model Artifact Handling & Promotion
- Required envs: `MODEL_PATH`, `MODEL_VERSION`, `MODEL_HASH`, `MODEL_DEVICE`. Validate path within allowed root; verify SHA256 before serving.
- Packaging options: (a) bake artifact into backend image layer for deterministic deploys; or (b) mount read-only volume/configured directory. Both carry version/hash metadata.
- Promotion: training pipeline emits artifact + `version/hash/device` manifest; copy artifact + manifest into the runtime artifact store and update envs/ConfigMap; readiness must show new version/hash before traffic.
- Rollback: keep N-1 artifact/manifest available; rollback by switching env/config to previous version/hash and redeploying; readiness blocks until hash matches.

## Probes and Runtime Settings
- Liveness: `/health/live` (process up).
- Readiness: `/health/ready` (model load + hash verified + config valid). Set initialDelay and failureThreshold to avoid flapping during load.
- Resource tuning: default `MODEL_DEVICE=cpu`; enable `cuda` only when nodes support it; specify node selectors/tolerations for GPU workloads.
- Concurrency/resource protection: `MAX_ACTIVE_GAMES` cap to avoid memory exhaustion; consider autoscaling on move latency and active games metrics.

## Deterministic/Test Modes
- `DETERMINISTIC_MODE=true` enables stubbed/deterministic agent and seeds; use only for tests/local debugging. Production should set false and rely on real model.
- Ensure CI smoke tests run readiness after setting deterministic mode with stubbed artifact to keep pipelines fast.***

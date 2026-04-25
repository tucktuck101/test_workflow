# Trainer Container and Jobs

This repo ships a standalone trainer container so training can run on-demand without coupling to the gameplay backend/frontend.

## Docker image
- `Dockerfile.trainer` builds a lightweight Python image containing `training/*` and `tools/`.
- Default envs: `TRAIN_OUTPUT=/app/artifacts`, `TRAIN_ARTIFACT_NAME=model.bin`, `TRAIN_EPOCHS=10`, `TRAIN_SEED=0`, `TRAIN_BOARD_SIZE=10`, `TRAIN_ALLOW_ADJACENT=true`. Override as needed.
- Volumes: mount `./artifacts` (rw) for outputs and `./configs` (ro) for any YAML/configs.

### Compose
`docker-compose.yml` includes a `trainer` service:
```bash
docker compose build trainer
docker compose run --rm trainer
```
Notes:
- No `depends_on` — backend/frontend do not require trainer to be running.
- Artifacts land in `./artifacts` and can be consumed by the backend container via the shared volume mount.

### Kubernetes
- `k8s/trainer-job.yaml`: one-off Job that mounts an `artifacts` PVC and `configs` ConfigMap.
- `k8s/trainer-cronjob.yaml`: scheduled run (default 3 AM daily). Adjust `schedule`/envs as needed.
Apply with:
```bash
kubectl apply -f k8s/trainer-job.yaml
# or
kubectl apply -f k8s/trainer-cronjob.yaml
```

## Running locally
```bash
# build trainer image
docker build -f Dockerfile.trainer -t battleship-trainer .
# run with artifacts/configs mounted
docker run --rm -v $(pwd)/artifacts:/app/artifacts -v $(pwd)/configs:/app/configs:ro battleship-trainer \
  python -m training.trainer
```

## Config/Artifacts
- Trainer reads configs via env vars; outputs artifacts/manifests to the mounted `TRAIN_OUTPUT`.
- Backend only needs the artifact/manifest on disk; it continues to serve even when trainer is not running.

## API-based orchestration (backend)
- Endpoints:
  - `POST /api/training/runs` to start a run (accepts optional `config` dict).
  - `GET /api/training/runs/{id}` to check status.
  - `POST /api/training/runs/{id}/cancel` to cancel.
- Status values: `pending`, `running`, `succeeded`, `failed`, `canceled`.
- Current orchestrator is a dummy/local simulator; Compose/K8s stubs are present to extend as needed.

## UI training control
- Frontend includes a Training page with YAML editor/upload, start/cancel controls, and run status display (backed by the endpoints above).

# Kubernetes Agent Guide

## Purpose
Use this guide for changes under `k8s/`. The root `AGENTS.md` still applies; this file covers Kubernetes trainer manifests and their relationship to local deployment docs.

## Local Source Truth
- `trainer-job.yaml` defines an on-demand trainer Job using the `battleship-trainer` image.
- `trainer-cronjob.yaml` defines a scheduled trainer CronJob using the same trainer command shape.
- `Dockerfile.trainer`, `docker-compose.yml`, `docs/DEPLOYMENT.md`, `docs/RUNBOOKS.md`, and `docs/ml/TRAINING_ORCHESTRATION.md` provide the surrounding deployment and orchestration context.

## Editing Guidance
- Keep trainer environment variables aligned with `training.trainer`, compose trainer settings, and deployment docs.
- Keep artifact and config volume assumptions explicit. Current manifests expect a `battleship-artifacts` PVC and `battleship-configs` ConfigMap.
- Treat these manifests as trainer workload definitions, not proof that the backend API launches Kubernetes Jobs.
- Preserve local-first and CPU-default assumptions unless the task explicitly introduces GPU or cluster-specific behavior.
- When changing image names, commands, env vars, or volume paths, check Dockerfiles and docs for matching references.

## Focused Checks
- If `kubectl` is available, prefer client-side validation such as `kubectl apply --dry-run=client -f k8s/trainer-job.yaml` and the matching CronJob command.
- If cluster tooling is unavailable, manually review YAML structure, env names, command, volume mounts, and referenced PVC/ConfigMap names.
- Check docs consistency with `docs/DEPLOYMENT.md`, `docs/RUNBOOKS.md`, and `docs/ml/TRAINING_ORCHESTRATION.md`.

## Docs Triggers
- Update `docs/DEPLOYMENT.md` when manifest behavior, env vars, image names, resources, or volume assumptions change.
- Update `docs/RUNBOOKS.md` when promotion, rollback, or trainer operation steps change.
- Update `docs/ml/TRAINING_ORCHESTRATION.md` only if orchestration behavior changes, not merely because manifests changed.
- Update `CODE_MAP.md` if deployment entrypoints or command surfaces change.

## Pitfalls
- Do not claim production Kubernetes orchestration exists just because manifests exist.
- Do not add cluster-specific secrets, paid cloud assumptions, or environment names without an explicit task.
- Do not rely on generated artifacts as deployment source truth.

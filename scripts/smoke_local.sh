#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.ci.yml}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-battleships-ci}"

cleanup() {
  docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" down --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "[smoke-local] Starting backend+frontend via $COMPOSE_FILE"
up_args=(--build)
if [[ "${COMPOSE_NO_BUILD:-false}" == "true" ]]; then
  up_args=(--no-build)
fi
docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" up -d "${up_args[@]}" backend frontend

echo "[smoke-local] Waiting for backend readiness"
ready=0
for _ in {1..30}; do
  if curl -sf http://localhost:8000/health/ready >/dev/null; then
    ready=1
    break
  fi
  sleep 2
done

if [[ "$ready" -ne 1 ]]; then
  docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" logs backend
  exit 1
fi

echo "[smoke-local] Starting a game"
curl -sf -X POST http://localhost:8000/api/games -o /tmp/battleships_smoke_start.json
cat /tmp/battleships_smoke_start.json
echo
echo "[smoke-local] Complete"

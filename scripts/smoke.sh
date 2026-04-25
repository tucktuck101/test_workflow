#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[smoke] Starting backend+frontend via docker compose..."
docker compose up -d backend frontend

echo "[smoke] Waiting for readiness..."
for i in {1..30}; do
  if curl -sf http://localhost:8000/health/ready >/dev/null; then
    echo "[smoke] Backend ready"
    break
  fi
  sleep 2
done

echo "[smoke] Hitting /api/games"
curl -sf -X POST http://localhost:8000/api/games -o /tmp/smoke_start.json
echo "[smoke] Response: $(cat /tmp/smoke_start.json)"

echo "[smoke] Cleaning up"
docker compose down

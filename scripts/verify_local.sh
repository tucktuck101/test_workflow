#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON:-.venv/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python"
fi

echo "[verify-local] Backend tests with coverage"
COVERAGE_THRESHOLD="${COVERAGE_THRESHOLD:-50}"

"$PYTHON_BIN" -m pytest \
  --maxfail=1 \
  --disable-warnings \
  --cov=app \
  --cov-fail-under="${COVERAGE_THRESHOLD}"

echo "[verify-local] Frontend typecheck, builds, and tests"
pushd frontend >/dev/null
npm run typecheck
npm run build
npm run build:training
npm test -- --coverage --watch=false
popd >/dev/null

echo "[verify-local] Training smoke"
./scripts/train_smoke.sh

echo "[verify-local] Complete"

#!/usr/bin/env bash
# Run baseline checks aligned with the Quality Gates Matrix.
# - Tests with coverage enforcement (default threshold configurable via COVERAGE_THRESHOLD).
# - Type checks where available.
# - Skips gracefully when no recognized project type is found; customize per stack.

set -euo pipefail

COVERAGE_THRESHOLD="${COVERAGE_THRESHOLD:-85}"
STATUS=0

info() { echo "[info] $*"; }
warn() { echo "[warn] $*" >&2; }

run_node() {
  if [[ -f package.json ]]; then
    info "Node project detected."
    if [[ -f package-lock.json ]]; then
      npm ci
    else
      npm install
    fi

    if npm run | grep -q "typecheck"; then
      info "Running npm run typecheck"
      npm run typecheck || STATUS=1
    else
      warn "No npm typecheck script found; skipping type checks."
    fi

    if npm run | grep -q "test"; then
      info "Running npm test with coverage"
      npm test -- --coverage --watch=false || STATUS=1
    else
      warn "No npm test script found; skipping tests/coverage."
    fi
  fi
}

run_python() {
  if [[ -f pyproject.toml || -f requirements.txt || -f requirements-dev.txt ]]; then
    info "Python project detected."
    python -m pip install --upgrade pip
    if [[ -f requirements.txt ]]; then
      python -m pip install -r requirements.txt
    fi
    if [[ -f requirements-dev.txt ]]; then
      python -m pip install -r requirements-dev.txt
    fi

    if command -v mypy >/dev/null 2>&1; then
      info "Running mypy type checks"
      mypy . || STATUS=1
    else
      warn "mypy not installed; skipping type checks."
    fi

    if command -v pytest >/dev/null 2>&1; then
      info "Running pytest with coverage threshold ${COVERAGE_THRESHOLD}%"
      pytest --maxfail=1 --disable-warnings --cov --cov-fail-under="${COVERAGE_THRESHOLD}" || STATUS=1
    else
      warn "pytest not installed; skipping tests/coverage."
    fi
  fi
}

run_node
run_python

if [[ "${STATUS}" -ne 0 ]]; then
  exit "${STATUS}"
fi

info "Quality gate checks completed."

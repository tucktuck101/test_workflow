#!/usr/bin/env bash
set -euo pipefail

OWNER="${OWNER:-tucktuck101}"
REPO="${REPO:-battleships-rl-platform}"
VISIBILITY="${VISIBILITY:-private}"
SOURCE_DIR="${SOURCE_DIR:-$(pwd)}"
IMPORT_DIR="${IMPORT_DIR:-/tmp/${REPO}-import}"

require() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

require gh
require git
require rsync

if [[ "$VISIBILITY" != "private" && "$VISIBILITY" != "public" ]]; then
  echo "VISIBILITY must be private or public." >&2
  exit 1
fi

rm -rf "$IMPORT_DIR"
mkdir -p "$IMPORT_DIR"

rsync -a "$SOURCE_DIR"/ "$IMPORT_DIR"/ \
  --exclude .git \
  --exclude .venv \
  --exclude .pytest_cache \
  --exclude .ruff_cache \
  --exclude .mypy_cache \
  --exclude frontend/node_modules \
  --exclude frontend/dist \
  --exclude frontend/dist-training \
  --exclude frontend/coverage \
  --exclude node_modules \
  --exclude artifacts \
  --exclude git_diag_\* \
  --exclude screencaps

pushd "$IMPORT_DIR" >/dev/null
git init
git checkout -b main
git add .
git commit -m "Initial Battleships RL platform import"

if gh repo view "${OWNER}/${REPO}" >/dev/null 2>&1; then
  echo "Repository ${OWNER}/${REPO} already exists; adding remote only."
  git remote add origin "https://github.com/${OWNER}/${REPO}.git" || true
else
  gh repo create "${OWNER}/${REPO}" "--${VISIBILITY}" --description "Battleships RL platform portfolio for AI training, model promotion, and SRE-oriented delivery." --source . --remote origin --push
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "https://github.com/${OWNER}/${REPO}.git"
fi

git push -u origin main
popd >/dev/null

echo "Created clean import at ${IMPORT_DIR}"
echo "Repository: https://github.com/${OWNER}/${REPO}"

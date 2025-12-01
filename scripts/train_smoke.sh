#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

OUT_DIR="$(mktemp -d)"
export TRAIN_OUTPUT="$OUT_DIR"
export TRAIN_EPOCHS=2
export TRAIN_SEED=123

python -m training.trainer
python -m tools.validate_artifact --artifact "$OUT_DIR/model.bin" --manifest "$OUT_DIR/manifest.json" --root "$OUT_DIR" --device cpu
python -m training.eval --artifact "$OUT_DIR/model.bin" --episodes 2 --board-size 5 --seed 123

rm -rf "$OUT_DIR"

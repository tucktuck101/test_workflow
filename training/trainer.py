import hashlib
import json
import os
import random
from dataclasses import asdict
from pathlib import Path
from typing import Dict

from .config import TrainConfig


class StubModel:
    """Tiny stub model whose 'training' is seeded RNG; produces deterministic bytes."""

    def __init__(self, seed: int, board_size: int) -> None:
        self.seed = seed
        self.board_size = board_size

    def train(self, epochs: int, lr: float) -> None:
        random.seed(self.seed)
        # Simulate training by advancing RNG.
        for _ in range(epochs * 10):
            random.random()
        self.lr = lr

    def export(self) -> bytes:
        random.seed(self.seed)
        payload = {
            "seed": self.seed,
            "board_size": self.board_size,
            "lr": getattr(self, "lr", None),
        }
        return json.dumps(payload, sort_keys=True).encode()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_artifact(output: Path, data: bytes) -> str:
    output.write_bytes(data)
    return sha256_bytes(data)


def write_manifest(output_dir: Path, artifact_path: Path, config: TrainConfig, hash_value: str) -> Path:
    manifest = {
        "version": config.version,
        "hash": hash_value,
        "device": config.device,
        "artifact": artifact_path.name,
        "board_size": config.board_size,
        "seed": config.seed,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest_path


def run_training(config: TrainConfig) -> Dict[str, str]:
    model = StubModel(seed=config.seed, board_size=config.board_size)
    model.train(epochs=config.epochs, lr=config.lr)
    artifact_path = config.output_dir / config.artifact_name
    artifact_hash = write_artifact(artifact_path, model.export())
    manifest_path = write_manifest(config.output_dir, artifact_path, config, artifact_hash)
    return {
        "artifact": str(artifact_path),
        "hash": artifact_hash,
        "manifest": str(manifest_path),
    }


def main() -> None:
    cfg = TrainConfig.from_env()
    results = run_training(cfg)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

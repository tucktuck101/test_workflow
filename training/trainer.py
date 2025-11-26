import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List

from .config import TrainConfig
from .env import BattleshipEnv
from .policy import QLearner


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_artifact(output: Path, policy: Dict[str, float]) -> str:
    payload = json.dumps(policy, sort_keys=True).encode()
    output.write_bytes(payload)
    return sha256_bytes(payload)


def write_manifest(output_dir: Path, artifact_path: Path, config: TrainConfig, hash_value: str, rewards: List[float]) -> Path:
    manifest = {
        "version": config.version,
        "hash": hash_value,
        "device": config.device,
        "artifact": artifact_path.name,
        "board_size": config.board_size,
        "seed": config.seed,
        "episodes": config.epochs,
        "lr": config.lr,
        "mean_reward": sum(rewards) / len(rewards) if rewards else 0.0,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest_path


def run_training(config: TrainConfig) -> Dict[str, str]:
    env = BattleshipEnv(board_size=config.board_size, seed=config.seed)
    learner = QLearner(env=env, epsilon=0.2, lr=config.lr)
    rewards = learner.train(config.epochs)
    artifact_path = config.output_dir / config.artifact_name
    artifact_hash = write_artifact(artifact_path, learner.export_policy())
    manifest_path = write_manifest(config.output_dir, artifact_path, config, artifact_hash, rewards)
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

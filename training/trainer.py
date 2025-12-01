import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List

from .config import TrainConfig
from .env import BattleshipEnv, DEFAULT_SHIPS
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
        "allow_adjacent": config.allow_adjacent,
        "ships": config.ships or DEFAULT_SHIPS,
        "seed": config.seed,
        "episodes": config.epochs,
        "lr": config.lr,
        "epsilon": config.epsilon,
        "epsilon_decay": config.epsilon_decay,
        "mean_reward": sum(rewards) / len(rewards) if rewards else 0.0,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest_path


def run_training(config: TrainConfig) -> Dict[str, str]:
    env = BattleshipEnv(
        board_size=config.board_size,
        seed=config.seed,
        allow_adjacent=config.allow_adjacent,
        ships=config.ships or list(DEFAULT_SHIPS),
        reward_step_base=config.reward_step_base,
        reward_step_decay=config.reward_step_decay,
        reward_step_cap=config.reward_step_cap,
        reward_hit=config.reward_hit,
        reward_miss=config.reward_miss,
        reward_sink_mult=config.reward_sink_mult,
        reward_win_max=config.reward_win_max,
        reward_win_decay_k=config.reward_win_decay_k,
        reward_loss=config.reward_loss,
        reward_perfect_move=config.reward_perfect_move,
    )
    learner = QLearner(env=env, epsilon=config.epsilon, epsilon_decay=config.epsilon_decay, lr=config.lr)
    print(
        f"[train] episodes={config.epochs} board={config.board_size} seed={config.seed} "
        f"lr={config.lr} epsilon={config.epsilon} decay={config.epsilon_decay} "
        f"allow_adjacent={config.allow_adjacent}",
        flush=True,
        file=sys.stderr,
    )
    progress_rewards: List[float] = []

    def progress(ep: int, reward: float, epsilon: float) -> None:
        progress_rewards.append(reward)
        if ep == 1 or ep % config.log_interval == 0 or ep == config.epochs:
            window = progress_rewards[-config.log_interval:] or progress_rewards
            window_mean = sum(window) / len(window)
            print(
                f"[train] ep {ep}/{config.epochs} reward={reward:.3f} "
                f"window_mean={window_mean:.3f} epsilon={epsilon:.3f}",
                flush=True,
                file=sys.stderr,
            )

    rewards = learner.train(config.epochs, progress_cb=progress)
    artifact_path = config.output_dir / config.artifact_name
    artifact_hash = write_artifact(artifact_path, learner.export_policy())
    manifest_path = write_manifest(config.output_dir, artifact_path, config, artifact_hash, rewards)
    print(f"[train] wrote artifact={artifact_path} manifest={manifest_path}", flush=True, file=sys.stderr)
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

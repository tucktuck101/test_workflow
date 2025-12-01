import csv
import json
import random
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from training.config import TrainConfig
from training.env import DEFAULT_SHIPS, BattleshipEnv
from training.policy import QLearner
from training.trainer import write_artifact

Coordinate = Tuple[int, int]
PolicyMap = Dict[Coordinate, float]


@dataclass
class SelfPlayConfig:
    episodes: int = 1000  # kept for backward compatibility; used if chunk_episodes is not set
    chunk_episodes: int = 0  # per training round; falls back to episodes when 0
    snapshot_interval: int = 100
    eval_games: int = 100
    win_threshold: float = 0.55
    loss_penalty: float = 5.0
    baseline_games: int = 0
    baseline_threshold: float = 0.0
    max_rounds: int = 1
    metrics_path: Optional[Path] = None

    @classmethod
    def from_env(cls) -> "SelfPlayConfig":
        import os

        episodes = int(os.getenv("SELFPLAY_EPISODES", "1000"))
        chunk = int(os.getenv("SELFPLAY_CHUNK_EPISODES", "0"))
        snapshot_interval = int(os.getenv("SELFPLAY_SNAPSHOT_INTERVAL", "100"))
        eval_games = int(os.getenv("SELFPLAY_EVAL_GAMES", "100"))
        win_threshold = float(os.getenv("SELFPLAY_THRESHOLD", "0.55"))
        loss_penalty = float(os.getenv("SELFPLAY_LOSS_PENALTY", "5.0"))
        baseline_games = int(os.getenv("SELFPLAY_BASELINE_GAMES", "0"))
        baseline_threshold = float(os.getenv("SELFPLAY_BASELINE_THRESHOLD", "0.0"))
        max_rounds = int(os.getenv("SELFPLAY_MAX_ROUNDS", "1"))
        metrics = os.getenv("SELFPLAY_METRICS_PATH")
        return cls(
            episodes=episodes,
            chunk_episodes=chunk,
            snapshot_interval=max(1, snapshot_interval),
            eval_games=eval_games,
            win_threshold=win_threshold,
            loss_penalty=loss_penalty,
            baseline_games=baseline_games,
            baseline_threshold=baseline_threshold,
            max_rounds=max(1, max_rounds),
            metrics_path=Path(metrics).expanduser().resolve() if metrics else None,
        )


def _policy_to_tuple_map(policy: Dict[str, float]) -> PolicyMap:
    out: PolicyMap = {}
    for key, val in policy.items():
        x, y = key.split(",")
        out[(int(x), int(y))] = float(val)
    return out


def _greedy_action(
    policy: Optional[PolicyMap], actions: List[Coordinate], rng: random.Random
) -> Coordinate:
    if not actions:
        return (0, 0)
    if not policy:
        return rng.choice(actions)
    return max(actions, key=lambda a: policy.get(a, 0.0))


def self_play_episode(
    learner: QLearner,
    env_me: BattleshipEnv,
    env_opp: BattleshipEnv,
    opponent_policy: Optional[PolicyMap],
    loss_penalty: float,
    rng: random.Random,
) -> Tuple[float, int, bool]:
    total_reward = 0.0
    moves = 0
    learner.env = env_opp

    while True:
        action = learner.select_action(explore=True)
        reward, _ = env_opp.step(action)
        learner.update(action, reward, env_opp.remaining == 0)
        total_reward += reward
        moves += 1

        if env_opp.remaining == 0:
            total_reward += 5.0
            return total_reward, moves, True

        op_action = _greedy_action(opponent_policy, env_me.available_actions(), rng)
        _, _ = env_me.step(op_action)
        if env_me.remaining == 0:
            total_reward -= loss_penalty
            return total_reward, moves, False

        if env_me.moves_taken >= env_me.max_moves or env_opp.moves_taken >= env_opp.max_moves:
            # Tie by move cap; treat as loss to discourage slow play
            total_reward -= loss_penalty / 2
            return total_reward, moves, False


def evaluate_policies(
    current_policy: PolicyMap,
    opponent_policy: Optional[PolicyMap],
    board_size: int,
    ships: List[Tuple[str, int]],
    allow_adjacent: bool,
    episodes: int,
    seed: int,
) -> Tuple[float, float]:
    rng = random.Random(seed)
    wins = 0
    total_moves = 0
    for _ in range(episodes):
        env_me = BattleshipEnv(
            board_size=board_size,
            seed=rng.randint(0, 10_000),
            ships=ships,
            allow_adjacent=allow_adjacent,
        )
        env_opp = BattleshipEnv(
            board_size=board_size,
            seed=rng.randint(0, 10_000),
            ships=ships,
            allow_adjacent=allow_adjacent,
        )
        moves = 0
        while True:
            action_me = _greedy_action(current_policy, env_opp.available_actions(), rng)
            env_opp.step(action_me)
            moves += 1
            if env_opp.remaining == 0:
                wins += 1
                total_moves += moves
                break
            action_opp = _greedy_action(opponent_policy, env_me.available_actions(), rng)
            env_me.step(action_opp)
            if env_me.remaining == 0:
                total_moves += moves
                break
            if env_me.moves_taken >= env_me.max_moves or env_opp.moves_taken >= env_opp.max_moves:
                total_moves += moves
                break
    win_rate = wins / episodes if episodes else 0.0
    mean_moves = total_moves / episodes if episodes else 0.0
    return win_rate, mean_moves


def write_selfplay_manifest(
    output_dir: Path,
    artifact_path: Path,
    config: TrainConfig,
    self_cfg: SelfPlayConfig,
    hash_value: str,
    rewards: List[float],
    win_rate: float,
    mean_moves: float,
    opponent_snapshot: PolicyMap,
    baseline_win_rate: Optional[float] = None,
    baseline_games: Optional[int] = None,
) -> Path:
    manifest = {
        "version": config.version,
        "hash": hash_value,
        "device": config.device,
        "artifact": artifact_path.name,
        "board_size": config.board_size,
        "allow_adjacent": config.allow_adjacent,
        "ships": config.ships or DEFAULT_SHIPS,
        "seed": config.seed,
        "episodes": self_cfg.episodes,
        "lr": config.lr,
        "epsilon": config.epsilon,
        "epsilon_decay": config.epsilon_decay,
        "mean_reward": sum(rewards) / len(rewards) if rewards else 0.0,
        "selfplay_win_rate": win_rate,
        "selfplay_mean_moves": mean_moves,
        "selfplay_eval_games": self_cfg.eval_games,
        "selfplay_threshold": self_cfg.win_threshold,
        "opponent_snapshot_size": len(opponent_snapshot),
    }
    if baseline_win_rate is not None:
        manifest["baseline_win_rate"] = baseline_win_rate
    if baseline_games is not None:
        manifest["baseline_eval_games"] = baseline_games
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest_path


def run_selfplay(config: TrainConfig, self_cfg: SelfPlayConfig) -> Dict[str, str]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rng = random.Random(config.seed)
    learner = QLearner(
        env=BattleshipEnv(
            board_size=config.board_size,
            seed=config.seed,
            ships=config.ships or DEFAULT_SHIPS,
            allow_adjacent=config.allow_adjacent,
        ),
        epsilon=config.epsilon,
        epsilon_decay=config.epsilon_decay,
        lr=config.lr,
    )

    rewards: List[float] = []
    wins = 0
    snapshot_policy: Optional[PolicyMap] = None
    metrics_path = self_cfg.metrics_path or (config.output_dir / f"selfplay_metrics-{run_id}.csv")
    metric_fields = [
        "phase",
        "round",
        "global_episode",
        "reward",
        "window_mean",
        "epsilon",
        "win_rate",
        "mean_moves",
        "baseline_win_rate",
    ]

    def log_metrics(row: Dict[str, float | int | None]) -> None:
        if not metrics_path:
            return
        write_header = not metrics_path.exists()
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with metrics_path.open("a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=metric_fields)
            if write_header:
                writer.writeheader()
            writer.writerow(row)

    chunk = self_cfg.chunk_episodes or self_cfg.episodes
    total_episodes = chunk * self_cfg.max_rounds

    print(
        f"[selfplay] chunk={chunk} max_rounds={self_cfg.max_rounds} total_episodes≈{total_episodes} "
        f"board={config.board_size} seed={config.seed} lr={config.lr} epsilon={config.epsilon} "
        f"decay={config.epsilon_decay} allow_adjacent={config.allow_adjacent}",
        file=sys.stderr,
        flush=True,
    )

    baseline_win_rate: Optional[float] = None

    for round_idx in range(1, self_cfg.max_rounds + 1):
        for ep in range(1, chunk + 1):
            global_ep = (round_idx - 1) * chunk + ep
            env_me = BattleshipEnv(
                board_size=config.board_size,
                seed=rng.randint(0, 10_000_000),
                ships=config.ships or DEFAULT_SHIPS,
                allow_adjacent=config.allow_adjacent,
            )
            env_opp = BattleshipEnv(
                board_size=config.board_size,
                seed=rng.randint(0, 10_000_000),
                ships=config.ships or DEFAULT_SHIPS,
                allow_adjacent=config.allow_adjacent,
            )
            reward, moves, win = self_play_episode(
                learner,
                env_me,
                env_opp,
                snapshot_policy,
                self_cfg.loss_penalty,
                rng,
            )
            rewards.append(reward)
            if win:
                wins += 1
            learner.epsilon *= learner.epsilon_decay
            if global_ep % self_cfg.snapshot_interval == 0:
                snapshot_policy = _policy_to_tuple_map(learner.export_policy())
            if (
                global_ep == 1
                or global_ep % config.log_interval == 0
                or (round_idx == self_cfg.max_rounds and ep == chunk)
            ):
                window = rewards[-config.log_interval :] or rewards
                window_mean = sum(window) / len(window)
                print(
                    f"[selfplay] ep {global_ep}/{total_episodes} reward={reward:.3f} "
                    f"window_mean={window_mean:.3f} epsilon={learner.epsilon:.3f}",
                    file=sys.stderr,
                    flush=True,
                )
                log_metrics(
                    {
                        "phase": "train",
                        "round": round_idx,
                        "global_episode": global_ep,
                        "reward": reward,
                        "window_mean": window_mean,
                        "epsilon": learner.epsilon,
                        "win_rate": None,
                        "mean_moves": None,
                        "baseline_win_rate": None,
                    }
                )

        current_policy = _policy_to_tuple_map(learner.export_policy())
        opponent_policy = snapshot_policy or current_policy

        # Baseline eval vs random
        if self_cfg.baseline_games > 0:
            baseline_win_rate, _ = evaluate_policies(
                current_policy,
                None,
                board_size=config.board_size,
                ships=config.ships or DEFAULT_SHIPS,
                allow_adjacent=config.allow_adjacent,
                episodes=self_cfg.baseline_games,
                seed=config.seed + round_idx,
            )
            print(
                f"[selfplay] round {round_idx}: baseline win_rate={baseline_win_rate:.3f} "
                f"games={self_cfg.baseline_games} threshold={self_cfg.baseline_threshold}",
                file=sys.stderr,
                flush=True,
            )
            log_metrics(
                {
                    "phase": "baseline_eval",
                    "round": round_idx,
                    "global_episode": round_idx * chunk,
                    "reward": None,
                    "window_mean": None,
                    "epsilon": learner.epsilon,
                    "win_rate": baseline_win_rate,
                    "mean_moves": None,
                    "baseline_win_rate": baseline_win_rate,
                }
            )
            if baseline_win_rate < self_cfg.baseline_threshold and round_idx < self_cfg.max_rounds:
                continue
            if baseline_win_rate < self_cfg.baseline_threshold and round_idx == self_cfg.max_rounds:
                raise RuntimeError(
                    f"baseline win_rate {baseline_win_rate:.3f} below threshold {self_cfg.baseline_threshold}"
                )

        win_rate, mean_moves = evaluate_policies(
            current_policy,
            opponent_policy,
            board_size=config.board_size,
            ships=config.ships or DEFAULT_SHIPS,
            allow_adjacent=config.allow_adjacent,
            episodes=self_cfg.eval_games,
            seed=config.seed + round_idx * 7,
        )

        print(
            f"[selfplay] round {round_idx}: selfplay win_rate={win_rate:.3f} mean_moves={mean_moves:.2f} "
            f"threshold={self_cfg.win_threshold}",
            file=sys.stderr,
            flush=True,
        )
        log_metrics(
            {
                "phase": "selfplay_eval",
                "round": round_idx,
                "global_episode": round_idx * chunk,
                "reward": None,
                "window_mean": None,
                "epsilon": learner.epsilon,
                "win_rate": win_rate,
                "mean_moves": mean_moves,
                "baseline_win_rate": baseline_win_rate,
            }
        )
        if win_rate >= self_cfg.win_threshold:
            artifact_path = config.output_dir / config.artifact_name
            artifact_hash = write_artifact(artifact_path, learner.export_policy())
            manifest_path = write_selfplay_manifest(
                config.output_dir,
                artifact_path,
                config,
                self_cfg,
                artifact_hash,
                rewards,
                win_rate,
                mean_moves,
                opponent_policy,
                baseline_win_rate=baseline_win_rate,
                baseline_games=self_cfg.baseline_games if self_cfg.baseline_games > 0 else None,
            )
            summary_path = config.output_dir / f"selfplay_run-{run_id}.json"
            summary = {
                "run_id": run_id,
                "metrics_path": str(metrics_path) if metrics_path else None,
                "artifact": str(artifact_path),
                "hash": artifact_hash,
                "manifest": str(manifest_path),
                "win_rate": win_rate,
                "baseline_win_rate": baseline_win_rate,
                "config": {
                    "train": {
                        "board_size": config.board_size,
                        "ships": config.ships or DEFAULT_SHIPS,
                        "allow_adjacent": config.allow_adjacent,
                        "epsilon": config.epsilon,
                        "epsilon_decay": config.epsilon_decay,
                        "lr": config.lr,
                        "seed": config.seed,
                    },
                    "selfplay": {
                        "chunk_episodes": chunk,
                        "max_rounds": self_cfg.max_rounds,
                        "snapshot_interval": self_cfg.snapshot_interval,
                        "eval_games": self_cfg.eval_games,
                        "threshold": self_cfg.win_threshold,
                        "baseline_games": self_cfg.baseline_games,
                        "baseline_threshold": self_cfg.baseline_threshold,
                        "loss_penalty": self_cfg.loss_penalty,
                        "run_id": run_id,
                    },
                },
            }
            summary_path.write_text(json.dumps(summary, indent=2))
            return summary
        # otherwise keep training next round

    raise RuntimeError(f"selfplay win_rate {win_rate:.3f} below threshold {self_cfg.win_threshold}")

    return {
        "artifact": str(artifact_path),
        "hash": artifact_hash,
        "manifest": str(manifest_path),
        "win_rate": win_rate,
    }


def main() -> None:
    cfg = TrainConfig.from_env()
    self_cfg = SelfPlayConfig.from_env()
    results = run_selfplay(cfg, self_cfg)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

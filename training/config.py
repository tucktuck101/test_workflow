from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


def _parse_bool(val: str, default: bool = True) -> bool:
    truthy = {"1", "true", "t", "yes", "y", "on"}
    falsy = {"0", "false", "f", "no", "n", "off"}
    lowered = val.strip().lower()
    if lowered in truthy:
        return True
    if lowered in falsy:
        return False
    return default


def _resolve(path: str) -> Path:
    return Path(path).expanduser().resolve()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class TrainConfig:
    output_dir: Path
    artifact_name: str
    seed: int = 0
    device: str = "cpu"
    epochs: int = 1
    lr: float = 0.01
    board_size: int = 10
    version: str = "dev"
    epsilon: float = 0.2
    epsilon_decay: float = 0.99
    log_interval: int = 10
    allow_adjacent: bool = True
    ships: Optional[List[Tuple[str, int]]] = None
    reward_step_base: float = -0.05
    reward_step_decay: float = 0.0
    reward_step_cap: float = -0.5
    reward_hit: float = 1.0
    reward_miss: float = 0.0
    reward_sink_mult: float = 1.0
    reward_win_max: float = 5.0
    reward_win_decay_k: float = 82.0
    reward_loss: float = -10.0
    reward_perfect_move: int = 17

    @classmethod
    def from_env(cls) -> "TrainConfig":
        import os

        output_dir = _resolve(os.getenv("TRAIN_OUTPUT", "./artifacts"))
        artifact_name = os.getenv("TRAIN_ARTIFACT_NAME", "model.bin")
        seed = int(os.getenv("TRAIN_SEED", "0"))
        device = os.getenv("TRAIN_DEVICE", "cpu")
        epochs = int(os.getenv("TRAIN_EPOCHS", "1"))
        lr = float(os.getenv("TRAIN_LR", "0.01"))
        board_size = 10
        version = os.getenv("TRAIN_VERSION", "dev")
        epsilon = float(os.getenv("TRAIN_EPSILON", "0.2"))
        epsilon_decay = float(os.getenv("TRAIN_EPSILON_DECAY", "0.99"))
        log_interval = max(1, int(os.getenv("TRAIN_LOG_INTERVAL", "10")))
        allow_adjacent = True
        reward_step_base = float(os.getenv("REWARD_STEP_BASE", "-0.05"))
        reward_step_decay = float(os.getenv("REWARD_STEP_DECAY", "0.0"))
        reward_step_cap = float(os.getenv("REWARD_STEP_CAP", "-0.5"))
        reward_hit = float(os.getenv("REWARD_HIT", "1.0"))
        reward_miss = float(os.getenv("REWARD_MISS", "0.0"))
        reward_sink_mult = float(os.getenv("REWARD_SINK_MULT", "1.0"))
        reward_win_max = float(os.getenv("REWARD_WIN_MAX", "5.0"))
        reward_win_decay_k = float(os.getenv("REWARD_WIN_DECAY_K", "82.0"))
        reward_loss = float(os.getenv("REWARD_LOSS", "-10.0"))
        reward_perfect_move = int(os.getenv("REWARD_PERFECT_MOVE", "17"))
        cfg = cls(
            output_dir=output_dir,
            artifact_name=artifact_name,
            seed=seed,
            device=device,
            epochs=epochs,
            lr=lr,
            board_size=board_size,
            version=version,
            epsilon=epsilon,
            epsilon_decay=epsilon_decay,
            log_interval=log_interval,
            allow_adjacent=allow_adjacent,
            reward_step_base=reward_step_base,
            reward_step_decay=reward_step_decay,
            reward_step_cap=reward_step_cap,
            reward_hit=reward_hit,
            reward_miss=reward_miss,
            reward_sink_mult=reward_sink_mult,
            reward_win_max=reward_win_max,
            reward_win_decay_k=reward_win_decay_k,
            reward_loss=reward_loss,
            reward_perfect_move=reward_perfect_move,
        )
        _ensure_parent(cfg.output_dir / cfg.artifact_name)
        return cfg

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


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
    board_size: int = 5
    version: str = "dev"

    @classmethod
    def from_env(cls) -> "TrainConfig":
        import os

        output_dir = _resolve(os.getenv("TRAIN_OUTPUT", "./artifacts"))
        artifact_name = os.getenv("TRAIN_ARTIFACT_NAME", "model.bin")
        seed = int(os.getenv("TRAIN_SEED", "0"))
        device = os.getenv("TRAIN_DEVICE", "cpu")
        epochs = int(os.getenv("TRAIN_EPOCHS", "1"))
        lr = float(os.getenv("TRAIN_LR", "0.01"))
        board_size = int(os.getenv("TRAIN_BOARD_SIZE", "5"))
        version = os.getenv("TRAIN_VERSION", "dev")
        cfg = cls(
            output_dir=output_dir,
            artifact_name=artifact_name,
            seed=seed,
            device=device,
            epochs=epochs,
            lr=lr,
            board_size=board_size,
            version=version,
        )
        _ensure_parent(cfg.output_dir / cfg.artifact_name)
        return cfg

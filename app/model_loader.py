from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ModelLoader:
    """Loads and validates a model artifact; placeholder for real RL model."""

    model_path: Path
    expected_hash: str
    device: str
    model_version: str
    ready: bool = False
    error: Optional[str] = None

    def __post_init__(self) -> None:
        try:
            self._validate_path()
            self._validate_hash()
            # Placeholder: in real implementation, load model here (PyTorch, etc.).
            self.ready = True
            self.error = None
        except Exception as exc:
            self.ready = False
            self.error = str(exc)

    def _validate_path(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError("missing_model")

    def _sha256(self) -> str:
        import hashlib

        hasher = hashlib.sha256()
        with self.model_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _validate_hash(self) -> None:
        digest = self._sha256()
        if digest.lower() != self.expected_hash.lower():
            raise ValueError("hash_mismatch")

    def assert_ready(self) -> None:
        if not self.ready:
            raise RuntimeError(self.error or "model_not_ready")

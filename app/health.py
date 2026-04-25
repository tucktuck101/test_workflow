import hashlib
from pathlib import Path
from typing import Dict

from .config import Settings
from .errors import raise_http
from .model_loader import ModelLoader


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def readiness_payload(settings: Settings, loader: ModelLoader) -> Dict:
    path = loader.model_path
    if settings.model_root:
        try:
            path.resolve().relative_to(settings.model_root.resolve())
        except Exception:
            raise_http("model_not_ready", {"reason": "path_outside_root"})
    if not path.exists():
        raise_http("model_not_ready", {"reason": "missing_model"})
    if not path.is_file():
        raise_http("model_not_ready", {"reason": "path_invalid"})

    try:
        digest = _sha256_file(path)
    except Exception:
        raise_http("model_not_ready", {"reason": "hash_compute_failed"})

    if digest.lower() != loader.expected_hash.lower():
        raise_http("model_not_ready", {"reason": "hash_mismatch"})

    return {
        "status": "ready",
        "model_version": loader.model_version,
        "model_hash": loader.expected_hash,
        "device": loader.device,
    }

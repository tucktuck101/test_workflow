import hashlib
from pathlib import Path
from typing import Dict

from .config import Settings
from .errors import raise_http


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def readiness_payload(settings: Settings) -> Dict:
    path = settings.model_path
    if not path.exists():
        raise_http("model_not_ready", {"reason": "missing_model"})

    try:
        digest = _sha256_file(path)
    except Exception:
        raise_http("model_not_ready", {"reason": "hash_compute_failed"})

    if digest.lower() != settings.model_hash.lower():
        raise_http("model_not_ready", {"reason": "hash_mismatch"})

    return {
        "status": "ready",
        "model_version": settings.model_version,
        "model_hash": settings.model_hash,
        "device": settings.model_device,
    }

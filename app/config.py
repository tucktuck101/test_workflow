import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _parse_bool(value: str, name: str) -> bool:
    truthy = {"1", "true", "t", "yes", "y", "on"}
    falsy = {"0", "false", "f", "no", "n", "off"}
    lowered = value.strip().lower()
    if lowered in truthy:
        return True
    if lowered in falsy:
        return False
    raise ValueError(f"{name} must be a boolean (true/false).")


def _parse_int(value: str, name: str, *, min_value: Optional[int] = None) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"{name} must be an integer.") from exc
    if min_value is not None and parsed < min_value:
        raise ValueError(f"{name} must be >= {min_value}.")
    return parsed


def _resolve_path(raw: str, name: str) -> Path:
    try:
        return Path(raw).expanduser().resolve()
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError(f"{name} must be a valid filesystem path.") from exc


@dataclass
class Settings:
    api_host: str
    api_port: int
    frontend_origin: Optional[str]
    model_root: Path
    model_path: Path
    model_version: str
    model_hash: str
    model_device: str
    board_size: int
    log_level: str
    observability_enabled: bool
    deterministic_mode: bool
    max_active_games: Optional[int]

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.environ

        api_host = env.get("API_HOST", "0.0.0.0")
        api_port = _parse_int(env.get("API_PORT", "8000"), "API_PORT", min_value=1)
        frontend_origin = env.get("FRONTEND_ORIGIN")

        model_path_raw = env.get("MODEL_PATH")
        if not model_path_raw:
            raise ValueError("MODEL_PATH is required.")
        model_path = _resolve_path(model_path_raw, "MODEL_PATH")

        model_root_raw = env.get("MODEL_ROOT")
        model_root = (
            _resolve_path(model_root_raw, "MODEL_ROOT")
            if model_root_raw
            else model_path.parent
        )
        if model_root not in (model_path, *model_path.parents):
            raise ValueError("MODEL_PATH must be within MODEL_ROOT.")

        model_version = env.get("MODEL_VERSION")
        if not model_version:
            raise ValueError("MODEL_VERSION is required.")

        model_hash = env.get("MODEL_HASH")
        if not model_hash:
            raise ValueError("MODEL_HASH is required.")

        model_device = env.get("MODEL_DEVICE", "cpu").lower()
        if model_device not in {"cpu", "cuda"}:
            raise ValueError("MODEL_DEVICE must be one of: cpu, cuda.")

        board_size = _parse_int(env.get("BOARD_SIZE", "10"), "BOARD_SIZE", min_value=1)

        log_level = env.get("LOG_LEVEL", "info").lower()
        if log_level not in {"debug", "info", "warning", "error", "critical"}:
            raise ValueError("LOG_LEVEL must be one of: debug, info, warning, error, critical.")

        observability_enabled = _parse_bool(
            env.get("OBSERVABILITY_ENABLED", "true"), "OBSERVABILITY_ENABLED"
        )
        deterministic_mode = _parse_bool(env.get("DETERMINISTIC_MODE", "false"), "DETERMINISTIC_MODE")

        max_active_games_raw = env.get("MAX_ACTIVE_GAMES", "100")
        max_active_games = _parse_int(max_active_games_raw, "MAX_ACTIVE_GAMES", min_value=1)

        return cls(
            api_host=api_host,
            api_port=api_port,
            frontend_origin=frontend_origin,
            model_root=model_root,
            model_path=model_path,
            model_version=model_version,
            model_hash=model_hash,
            model_device=model_device,
            board_size=board_size,
            log_level=log_level,
            observability_enabled=observability_enabled,
            deterministic_mode=deterministic_mode,
            max_active_games=max_active_games,
        )

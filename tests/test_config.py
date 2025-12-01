from pathlib import Path

import pytest

from app.config import Settings
from app.main import create_app


def _set_common_env(monkeypatch, tmp_path: Path) -> Path:
    for key in (
        "MODEL_PATH",
        "MODEL_VERSION",
        "MODEL_HASH",
        "MODEL_DEVICE",
        "BOARD_SIZE",
        "MAX_ACTIVE_GAMES",
        "OBSERVABILITY_ENABLED",
        "DETERMINISTIC_MODE",
        "API_PORT",
        "API_HOST",
        "FRONTEND_ORIGIN",
        "MODEL_ROOT",
    ):
        monkeypatch.delenv(key, raising=False)
    model_path = tmp_path / "model.bin"
    model_path.write_bytes(b"stub")
    monkeypatch.setenv("MODEL_PATH", str(model_path))
    monkeypatch.setenv("MODEL_VERSION", "v0.0.1")
    monkeypatch.setenv("MODEL_HASH", "sha256stub")
    return model_path


def test_settings_from_env_valid(monkeypatch, tmp_path):
    model_path = _set_common_env(monkeypatch, tmp_path)
    monkeypatch.setenv("MODEL_DEVICE", "cpu")
    monkeypatch.setenv("BOARD_SIZE", "10")
    monkeypatch.setenv("MAX_ACTIVE_GAMES", "5")
    monkeypatch.setenv("OBSERVABILITY_ENABLED", "true")
    monkeypatch.setenv("DETERMINISTIC_MODE", "false")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setenv("FRONTEND_ORIGIN", "http://localhost:5173")
    monkeypatch.setenv("MODEL_ROOT", str(model_path.parent))

    settings = Settings.from_env()

    assert settings.model_path == model_path.resolve()
    assert settings.model_root == model_path.parent.resolve()
    assert settings.model_device == "cpu"
    assert settings.board_size == 10
    assert settings.max_active_games == 5
    assert settings.api_port == 9000
    assert settings.api_host == "127.0.0.1"
    assert settings.frontend_origin == "http://localhost:5173"
    assert settings.observability_enabled is True
    assert settings.deterministic_mode is False


def test_settings_missing_required(monkeypatch):
    for key in ("MODEL_PATH", "MODEL_VERSION", "MODEL_HASH"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(ValueError):
        Settings.from_env()


def test_settings_rejects_path_outside_root(monkeypatch, tmp_path):
    _set_common_env(monkeypatch, tmp_path)
    outside_root = tmp_path / "other"
    outside_root.mkdir()
    model_path = outside_root / "model.bin"
    model_path.write_bytes(b"stub")
    monkeypatch.setenv("MODEL_PATH", str(model_path))
    monkeypatch.setenv("MODEL_ROOT", str(tmp_path / "root"))

    with pytest.raises(ValueError):
        Settings.from_env()


def test_settings_rejects_invalid_device(monkeypatch, tmp_path):
    _set_common_env(monkeypatch, tmp_path)
    monkeypatch.setenv("MODEL_DEVICE", "tpu")
    with pytest.raises(ValueError):
        Settings.from_env()


def test_settings_rejects_invalid_board_size(monkeypatch, tmp_path):
    _set_common_env(monkeypatch, tmp_path)
    monkeypatch.setenv("BOARD_SIZE", "0")
    with pytest.raises(ValueError):
        Settings.from_env()


def test_create_app_smoke(monkeypatch, tmp_path):
    _set_common_env(monkeypatch, tmp_path)
    settings = Settings.from_env()
    app = create_app(settings)
    assert app.state.settings.model_version == "v0.0.1"

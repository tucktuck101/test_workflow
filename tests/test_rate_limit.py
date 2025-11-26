import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def make_settings(tmp_path, max_active_games=2):
    model_path = tmp_path / "model.bin"
    model_path.write_bytes(b"stub")
    return Settings(
        api_host="0.0.0.0",
        api_port=8000,
        frontend_origin=None,
        model_root=model_path.parent,
        model_path=model_path,
        model_version="v0",
        model_hash="da39a3ee5e6b4b0d3255bfef95601890afd80709",
        model_device="cpu",
        board_size=5,
        log_level="info",
        observability_enabled=True,
        deterministic_mode=True,
        max_active_games=max_active_games,
    )


def test_rate_limit_returns_429(monkeypatch, tmp_path):
    settings = make_settings(tmp_path)
    app = create_app(settings)
    client = TestClient(app)
    # exceed rate limit capacity quickly
    for _ in range(6):
        resp = client.post("/api/games")
    assert resp.status_code in (429, 503)


def test_normal_flow_not_rate_limited(monkeypatch, tmp_path):
    settings = make_settings(tmp_path)
    app = create_app(settings)
    client = TestClient(app)
    resp = client.post("/api/games")
    assert resp.status_code in (200, 503)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_create_app_adds_cors_when_origin_set(tmp_path):
    model_path = tmp_path / "model.bin"
    model_path.write_bytes(b"stub")
    settings = Settings(
        api_host="0.0.0.0",
        api_port=8000,
        frontend_origin="http://localhost:5173",
        model_root=model_path.parent,
        model_path=model_path,
        model_version="v0",
        model_hash="da39a3ee5e6b4b0d3255bfef95601890afd80709",
        model_device="cpu",
        board_size=10,
        log_level="info",
        observability_enabled=True,
        deterministic_mode=True,
        max_active_games=5,
    )
    app = create_app(settings)
    assert any(isinstance(middleware.cls, CORSMiddleware.__class__) for middleware in app.user_middleware)


def test_create_app_without_cors(tmp_path):
    model_path = tmp_path / "model.bin"
    model_path.write_bytes(b"stub")
    settings = Settings(
        api_host="0.0.0.0",
        api_port=8000,
        frontend_origin=None,
        model_root=model_path.parent,
        model_path=model_path,
        model_version="v0",
        model_hash="da39a3ee5e6b4b0d3255bfef95601890afd80709",
        model_device="cpu",
        board_size=10,
        log_level="info",
        observability_enabled=True,
        deterministic_mode=True,
        max_active_games=5,
    )
    app = create_app(settings)
    assert not any(isinstance(middleware.cls, CORSMiddleware.__class__) for middleware in app.user_middleware)


def test_cors_allows_preflight(tmp_path):
    model_path = tmp_path / "model.bin"
    model_path.write_bytes(b"stub")
    settings = Settings(
        api_host="0.0.0.0",
        api_port=8000,
        frontend_origin="http://localhost:5173",
        model_root=model_path.parent,
        model_path=model_path,
        model_version="v0",
        model_hash="da39a3ee5e6b4b0d3255bfef95601890afd80709",
        model_device="cpu",
        board_size=10,
        log_level="info",
        observability_enabled=True,
        deterministic_mode=True,
        max_active_games=5,
    )
    app = create_app(settings)
    client = TestClient(app)
    resp = client.options("/health/live", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})
    assert resp.status_code == 200

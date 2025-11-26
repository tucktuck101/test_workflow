import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _write_stub(path: Path, content: bytes = b"stub") -> str:
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def _make_app(tmp_path: Path, content: bytes = b"stub"):
    model_path = tmp_path / "model.bin"
    model_hash = _write_stub(model_path, content)
def test_readiness_success(monkeypatch, tmp_path):
    model_path = tmp_path / "model.bin"
    expected_hash = _write_stub(model_path)
    monkeypatch.setenv("MODEL_PATH", str(model_path))
    monkeypatch.setenv("MODEL_VERSION", "v0.0.1")
    monkeypatch.setenv("MODEL_HASH", expected_hash)
    monkeypatch.setenv("MODEL_DEVICE", "cpu")

    settings = Settings.from_env()
    app = create_app(settings)
    client = TestClient(app)

    resp = client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["model_hash"] == expected_hash


def test_readiness_missing_file(monkeypatch, tmp_path):
    model_path = tmp_path / "missing.bin"
    # create a file but use wrong hash to simulate not-ready state
    _write_stub(model_path, b"stub")
    monkeypatch.setenv("MODEL_PATH", str(model_path))
    monkeypatch.setenv("MODEL_VERSION", "v0.0.1")
    monkeypatch.setenv("MODEL_HASH", "deadbeef")
    monkeypatch.setenv("MODEL_DEVICE", "cpu")

    settings = Settings.from_env()
    app = create_app(settings)
    client = TestClient(app)

    resp = client.get("/health/ready")
    assert resp.status_code == 503
    assert resp.json()["detail"]["error_code"] == "model_not_ready"


def test_readiness_hash_mismatch(monkeypatch, tmp_path):
    model_path = tmp_path / "model.bin"
    _write_stub(model_path, b"foo")
    monkeypatch.setenv("MODEL_PATH", str(model_path))
    monkeypatch.setenv("MODEL_VERSION", "v0.0.1")
    monkeypatch.setenv("MODEL_HASH", "bad_hash")
    monkeypatch.setenv("MODEL_DEVICE", "cpu")

    settings = Settings.from_env()
    app = create_app(settings)
    client = TestClient(app)

    resp = client.get("/health/ready")
    assert resp.status_code == 503
    assert resp.json()["detail"]["error_code"] == "model_not_ready"


def test_liveness():
    settings = Settings(
        api_host="0.0.0.0",
        api_port=8000,
        frontend_origin=None,
        model_root=Path("."),
        model_path=Path("."),
        model_version="v0",
        model_hash="hash",
        model_device="cpu",
        board_size=10,
        log_level="info",
        observability_enabled=True,
        deterministic_mode=False,
        max_active_games=None,
    )
    app = create_app(settings)
    client = TestClient(app)
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

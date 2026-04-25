import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.model_loader import ModelLoader


def _write_stub(path: Path, content: bytes = b"stub") -> str:
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def _prepare_env(monkeypatch, tmp_path: Path, *, hash_value: str | None = None) -> str:
    model_path = tmp_path / "model.bin"
    digest = _write_stub(model_path)
    if hash_value:
        digest = hash_value
    monkeypatch.setenv("MODEL_PATH", str(model_path))
    monkeypatch.setenv("MODEL_VERSION", "v0.0.1")
    monkeypatch.setenv("MODEL_HASH", digest)
    monkeypatch.setenv("MODEL_DEVICE", "cpu")
    return digest


def test_readiness_success(monkeypatch, tmp_path):
    expected_hash = _prepare_env(monkeypatch, tmp_path)

    settings = Settings.from_env()
    app = create_app(settings)
    client = TestClient(app)

    resp = client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["model_hash"] == expected_hash


def test_readiness_missing_file(monkeypatch, tmp_path):
    missing = tmp_path / "missing.bin"
    monkeypatch.setenv("MODEL_PATH", str(missing))
    monkeypatch.setenv("MODEL_VERSION", "v0.0.1")
    monkeypatch.setenv("MODEL_HASH", "deadbeef")
    monkeypatch.setenv("MODEL_DEVICE", "cpu")
    monkeypatch.setenv("MODEL_ROOT", str(tmp_path))

    settings = Settings.from_env()
    app = create_app(settings)
    client = TestClient(app)

    resp = client.get("/health/ready")
    assert resp.status_code == 503
    body = resp.json()
    assert body["detail"]["error_code"] == "model_not_ready"
    assert body["detail"]["details"]["reason"] == "missing_model"


def test_readiness_hash_mismatch(monkeypatch, tmp_path):
    _prepare_env(monkeypatch, tmp_path, hash_value="bad_hash")
    settings = Settings.from_env()
    app = create_app(settings)
    client = TestClient(app)

    resp = client.get("/health/ready")
    assert resp.status_code == 503
    assert resp.json()["detail"]["details"]["reason"] == "hash_mismatch"


def test_readiness_path_outside_root(tmp_path):
    # Build settings manually to bypass env validation and hit readiness with a disallowed path.
    model_root = tmp_path / "allowed"
    outside = tmp_path / "other" / "model.bin"
    outside.parent.mkdir()
    outside.write_bytes(b"stub")
    settings = Settings(
        api_host="0.0.0.0",
        api_port=8000,
        frontend_origin=None,
        model_root=model_root,
        model_path=outside,
        model_version="v0",
        model_hash=hashlib.sha256(b"stub").hexdigest(),
        model_device="cpu",
        board_size=10,
        log_level="info",
        observability_enabled=True,
        deterministic_mode=False,
        max_active_games=10,
    )
    app = create_app(settings)
    client = TestClient(app)

    resp = client.get("/health/ready")
    assert resp.status_code == 503
    assert resp.json()["detail"]["details"]["reason"] == "path_outside_root"


def test_readiness_load_failure(monkeypatch, tmp_path):
    _prepare_env(monkeypatch, tmp_path)

    def _boom(self):
        raise RuntimeError("load_failed")

    monkeypatch.setattr(ModelLoader, "_sha256", _boom)
    settings = Settings.from_env()
    app = create_app(settings)
    client = TestClient(app)

    resp = client.get("/health/ready")
    assert resp.status_code == 503
    assert resp.json()["detail"]["details"]["reason"] == "load_failed"


def test_liveness(tmp_path):
    model_path = tmp_path / "model.bin"
    model_path.write_bytes(b"stub")
    settings = Settings(
        api_host="0.0.0.0",
        api_port=8000,
        frontend_origin=None,
        model_root=model_path.parent,
        model_path=model_path,
        model_version="v0",
        model_hash=hashlib.sha256(b"stub").hexdigest(),
        model_device="cpu",
        board_size=10,
        log_level="info",
        observability_enabled=True,
        deterministic_mode=False,
        max_active_games=5,
    )
    app = create_app(settings)
    client = TestClient(app)
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_readiness_path_invalid(tmp_path):
    model_dir = tmp_path / "dir_model"
    model_dir.mkdir()
    settings = Settings(
        api_host="0.0.0.0",
        api_port=8000,
        frontend_origin=None,
        model_root=model_dir.parent,
        model_path=model_dir,
        model_version="v0",
        model_hash="deadbeef",
        model_device="cpu",
        board_size=10,
        log_level="info",
        observability_enabled=True,
        deterministic_mode=False,
        max_active_games=5,
    )
    app = create_app(settings)
    client = TestClient(app)
    resp = client.get("/health/ready")
    assert resp.status_code == 503
    assert resp.json()["detail"]["details"]["reason"] == "path_invalid"


def test_readiness_hash_compute_failure(monkeypatch, tmp_path):
    _prepare_env(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "app.health._sha256_file", lambda _: (_ for _ in ()).throw(ValueError("boom"))
    )
    settings = Settings.from_env()
    app = create_app(settings)
    client = TestClient(app)
    resp = client.get("/health/ready")
    assert resp.status_code == 503
    assert resp.json()["detail"]["details"]["reason"] == "hash_compute_failed"

import hashlib
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _make_app(tmp_path: Path) -> TestClient:
    model_path = tmp_path / "model.bin"
    model_path.write_bytes(b"stub-model")
    model_hash = hashlib.sha256(model_path.read_bytes()).hexdigest()
    settings = Settings(
        api_host="0.0.0.0",
        api_port=8000,
        frontend_origin=None,
        model_root=model_path.parent,
        model_path=model_path,
        model_version="test",
        model_hash=model_hash,
        model_device="cpu",
        board_size=5,
        log_level="debug",
        observability_enabled=False,
        deterministic_mode=True,
        max_active_games=5,
    )
    app = create_app(settings)
    return TestClient(app)


def test_start_training_run_succeeds(tmp_path):
    client = _make_app(tmp_path)
    resp = client.post("/api/training/runs", json={"config": {"epochs": 1}})
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]
    assert resp.json()["status"] in {"pending", "running"}

    # wait for completion
    time.sleep(0.2)
    status = client.get(f"/api/training/runs/{run_id}")
    assert status.status_code == 200
    assert status.json()["status"] in {"running", "succeeded"}


def test_cancel_training_run(tmp_path):
    client = _make_app(tmp_path)
    resp = client.post("/api/training/runs", json={"config": {"epochs": 1}})
    run_id = resp.json()["run_id"]

    cancel = client.post(f"/api/training/runs/{run_id}/cancel")
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "canceled"


def test_training_run_failure(tmp_path):
    client = _make_app(tmp_path)
    resp = client.post("/api/training/runs", json={"config": {"fail": True}})
    run_id = resp.json()["run_id"]
    time.sleep(0.2)
    status = client.get(f"/api/training/runs/{run_id}")
    assert status.status_code == 200
    assert status.json()["status"] in {"failed", "running"}


def test_training_metrics(tmp_path):
    client = _make_app(tmp_path)
    resp = client.post("/api/training/runs", json={"config": {"epochs": 1}})
    run_id = resp.json()["run_id"]
    metrics_resp = client.get(f"/api/training/runs/{run_id}/metrics")
    assert metrics_resp.status_code == 200
    body = metrics_resp.json()
    assert body["run_id"] == run_id
    assert "episodes" in body["metrics"]

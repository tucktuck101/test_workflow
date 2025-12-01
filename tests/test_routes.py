import hashlib
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _make_app(monkeypatch, tmp_path: Path, **env_overrides):
    content = b"stub"
    model_path = tmp_path / "model.bin"
    model_hash = hashlib.sha256(content).hexdigest()
    model_path.write_bytes(content)

    monkeypatch.setenv("MODEL_PATH", str(model_path))
    monkeypatch.setenv("MODEL_VERSION", "v0.0.1")
    monkeypatch.setenv("MODEL_HASH", model_hash)
    monkeypatch.setenv("MODEL_DEVICE", "cpu")
    monkeypatch.setenv("BOARD_SIZE", str(env_overrides.get("BOARD_SIZE", 10)))
    monkeypatch.setenv("DETERMINISTIC_MODE", str(env_overrides.get("DETERMINISTIC_MODE", "true")))
    monkeypatch.setenv("MAX_ACTIVE_GAMES", str(env_overrides.get("MAX_ACTIVE_GAMES", 2)))
    monkeypatch.setenv("MODEL_ROOT", str(model_path.parent))

    settings = Settings.from_env()
    app = create_app(settings)
    return TestClient(app)


def test_start_and_move_flow(monkeypatch, tmp_path):
    client = _make_app(monkeypatch, tmp_path)

    start_resp = client.post("/api/games")
    assert start_resp.status_code == 200
    game_id = start_resp.json()["game_id"]

    move_resp = client.post(f"/api/games/{game_id}/moves", json={"x": 0, "y": 0})
    assert move_resp.status_code == 200
    data = move_resp.json()
    assert "player_result" in data
    assert data["status"] in {"in_progress", "player_won", "agent_won"}


def test_start_with_placements(monkeypatch, tmp_path):
    client = _make_app(monkeypatch, tmp_path)
    placements = {
        "placements": [
            {"name": "Carrier", "coordinates": [[0, 0], [1, 0], [2, 0], [3, 0], [4, 0]]},
            {"name": "Battleship", "coordinates": [[0, 1], [1, 1], [2, 1], [3, 1]]},
            {"name": "Cruiser", "coordinates": [[0, 2], [1, 2], [2, 2]]},
            {"name": "Submarine", "coordinates": [[0, 3], [1, 3], [2, 3]]},
            {"name": "Destroyer", "coordinates": [[0, 4], [1, 4]]},
        ]
    }
    resp = client.post("/api/games", json=placements)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "in_progress"

def test_duplicate_move_returns_400(monkeypatch, tmp_path):
    client = _make_app(monkeypatch, tmp_path)
    game_id = client.post("/api/games").json()["game_id"]
    first = client.post(f"/api/games/{game_id}/moves", json={"x": 0, "y": 0})
    assert first.status_code == 200

    dup = client.post(f"/api/games/{game_id}/moves", json={"x": 0, "y": 0})
    assert dup.status_code == 400
    assert dup.json()["detail"]["error_code"] == "duplicate_move"


def test_game_not_found(monkeypatch, tmp_path):
    client = _make_app(monkeypatch, tmp_path)
    missing = uuid.uuid4()
    resp = client.post(f"/api/games/{missing}/moves", json={"x": 0, "y": 0})
    assert resp.status_code == 404
    assert resp.json()["detail"]["error_code"] == "game_not_found"


def test_capacity_cap(monkeypatch, tmp_path):
    client = _make_app(monkeypatch, tmp_path, MAX_ACTIVE_GAMES=1)
    first = client.post("/api/games")
    assert first.status_code == 200

    second = client.post("/api/games")
    assert second.status_code == 429
    assert second.json()["detail"]["error_code"] == "capacity_exceeded"


def test_quit_is_idempotent(monkeypatch, tmp_path):
    client = _make_app(monkeypatch, tmp_path)
    game_id = client.post("/api/games").json()["game_id"]

    resp1 = client.post(f"/api/games/{game_id}/quit")
    resp2 = client.post(f"/api/games/{game_id}/quit")

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "ended"


def test_inference_failure_aborts_game(monkeypatch, tmp_path):
    client = _make_app(monkeypatch, tmp_path)

    def _boom(self, session):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.agent.AgentAdapter.next_move", _boom)
    game_id = client.post("/api/games").json()["game_id"]
    resp = client.post(f"/api/games/{game_id}/moves", json={"x": 0, "y": 0})
    assert resp.status_code == 503
    assert resp.json()["detail"]["error_code"] == "inference_failed"

    # subsequent moves should now see the game as finished/aborted
    resp2 = client.post(f"/api/games/{game_id}/moves", json={"x": 1, "y": 1})
    assert resp2.status_code == 409

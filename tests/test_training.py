import json
from pathlib import Path

from training.config import TrainConfig
from training.trainer import run_training, sha256_bytes
from tools.validate_artifact import main as validate_main


def test_training_deterministic(tmp_path: Path):
    cfg = TrainConfig(
        output_dir=tmp_path,
        artifact_name="model.bin",
        seed=42,
        device="cpu",
        epochs=1,
        lr=0.01,
        board_size=5,
        version="v-test",
    )
    result = run_training(cfg)
    artifact = Path(result["artifact"])
    manifest = Path(result["manifest"])

    assert artifact.exists()
    assert manifest.exists()

    data = artifact.read_bytes()
    digest = sha256_bytes(data)
    assert digest == result["hash"]

    manifest_data = json.loads(manifest.read_text())
    assert manifest_data["version"] == "v-test"
    assert manifest_data["hash"] == digest
    assert manifest_data["device"] == "cpu"
    # deterministic export content
    cfg2 = cfg
    cfg2.seed = 42
    again = run_training(cfg2)
    assert Path(again["artifact"]).read_bytes() == data


def test_validate_artifact_success(tmp_path: Path, capsys):
    cfg = TrainConfig(
        output_dir=tmp_path,
        artifact_name="model.bin",
        seed=1,
        device="cpu",
        epochs=1,
        lr=0.01,
        board_size=5,
        version="v-test",
    )
    res = run_training(cfg)
    code = validate_main(
        [
            "--artifact",
            res["artifact"],
            "--manifest",
            res["manifest"],
            "--root",
            str(tmp_path),
            "--device",
            "cpu",
        ]
    )
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert code == 0
    assert data["status"] == "ok"
    assert data["version"] == "v-test"


def test_validate_artifact_hash_mismatch(tmp_path: Path, capsys):
    artifact = tmp_path / "model.bin"
    manifest = tmp_path / "manifest.json"
    artifact.write_bytes(b"abc")
    manifest.write_text(json.dumps({"hash": "deadbeef", "device": "cpu"}))
    code = validate_main(
        ["--artifact", str(artifact), "--manifest", str(manifest), "--root", str(tmp_path)]
    )
    data = json.loads(capsys.readouterr().out)
    assert code == 1
    assert data["reason"] == "hash_mismatch"

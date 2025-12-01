import json
from pathlib import Path

from training.config import TrainConfig
from training.env import BattleshipEnv
from training.trainer import run_training, sha256_bytes
from training.eval import evaluate as eval_policy
from training.selfplay_trainer import run_selfplay, SelfPlayConfig
from training.dqn_selfplay import run_dqn_selfplay, DQNConfig as DQNSelfCfg, SelfPlayConfig as DQNSelfPlayCfg
from tools.validate_artifact import main as validate_main
from training.state_encoder import encode_state


def test_training_deterministic(tmp_path: Path):
    cfg = TrainConfig(
        output_dir=tmp_path,
        artifact_name="model.bin",
        seed=42,
        device="cpu",
        epochs=5,
        lr=0.1,
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
    assert manifest_data["episodes"] == cfg.epochs
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


def test_env_step_rewards():
    env = BattleshipEnv(board_size=3, seed=0, ships=[("Dest", 1)])
    env.reset()
    reward, done = env.step((0, 0))
    # first move at least incurs step penalty
    assert reward <= 1.0
    assert done in {True, False}


def test_reward_shaping_win_bonus():
    env = BattleshipEnv(
        board_size=3,
        seed=0,
        ships=[("Dest", 1)],
        reward_step_base=0.0,
        reward_step_decay=0.0,
        reward_step_cap=-1.0,
        reward_hit=0.0,
        reward_miss=0.0,
        reward_sink_mult=0.0,
        reward_win_max=10.0,
        reward_win_decay_k=1.0,
        reward_loss=-5.0,
        reward_perfect_move=1,
    )
    # Force deterministic ship placement at (0,0)
    env.agent_board = [(0, 0)]
    env.ship_cells = [{(0, 0)}]
    env.cell_to_ship = {(0, 0): 0}
    env.ship_remaining = [1]
    env.remaining = 1
    env.hits = set()
    env.misses = set()
    env.moves_taken = 0
    reward, done = env.step((0, 0))
    assert done is True
    assert reward == 10.0  # pure win bonus at perfect move


def test_reward_shaping_decay_penalty():
    env = BattleshipEnv(
        board_size=3,
        seed=0,
        ships=[("Dest", 1)],
        reward_step_base=0.0,
        reward_step_decay=1.0,
        reward_step_cap=-0.5,
        reward_hit=0.0,
        reward_miss=0.0,
        reward_sink_mult=0.0,
        reward_win_max=0.0,
        reward_win_decay_k=1.0,
        reward_loss=0.0,
        reward_perfect_move=1,
        max_moves=200,
    )
    # Place ship away from (0,0) and fast-forward moves to trigger decay
    env.agent_board = [(2, 2)]
    env.ship_cells = [{(2, 2)}]
    env.cell_to_ship = {(2, 2): 0}
    env.ship_remaining = [1]
    env.remaining = 1
    env.hits = set()
    env.misses = set()
    env.moves_taken = 17  # step will increment to 18
    reward, done = env.step((0, 0))
    assert done is False
    assert reward == -0.5  # capped decay penalty


def test_eval_policy(tmp_path: Path):
    cfg = TrainConfig(
        output_dir=tmp_path,
        artifact_name="model.bin",
        seed=1,
        device="cpu",
        epochs=3,
        lr=0.1,
        board_size=3,
        version="v-eval",
        ships=[("Dest", 1), ("Sub", 2)],
    )
    res = run_training(cfg)
    mean_reward, mean_moves = eval_policy(
        Path(res["artifact"]),
        episodes=3,
        board_size=cfg.board_size,
        seed=cfg.seed,
        ships=cfg.ships,
        allow_adjacent=cfg.allow_adjacent,
    )
    assert mean_moves > 0
    # trained policy should not be catastrophically bad
    assert mean_reward > -5


def test_selfplay_training_with_gate(tmp_path: Path):
    cfg = TrainConfig(
        output_dir=tmp_path,
        artifact_name="model.bin",
        seed=2,
        device="cpu",
        epochs=10,  # unused by selfplay but kept for manifest fields
        lr=0.1,
        board_size=3,
        version="v-selfplay",
        ships=[("Dest", 1), ("Sub", 2)],
        allow_adjacent=True,
    )
    self_cfg = SelfPlayConfig(
        episodes=10,
        chunk_episodes=5,
        max_rounds=2,
        snapshot_interval=2,
        eval_games=5,
        win_threshold=0.0,  # ensure gate passes
        loss_penalty=2.0,
        baseline_games=5,
        baseline_threshold=0.0,
    )
    res = run_selfplay(cfg, self_cfg)
    assert Path(res["artifact"]).exists()
    assert Path(res["manifest"]).exists()
    assert res["win_rate"] >= self_cfg.win_threshold


def test_state_encoder_shapes():
    env = BattleshipEnv(board_size=3, seed=0, ships=[("Dest", 1)])
    env.hits = {(0, 0)}
    env.misses = {(1, 1)}
    env.moves_taken = 2
    encoded = encode_state(env, last_player_shot=(0, 0), last_agent_shot=(1, 2), include_self=False, include_hit_cluster=True)
    # channels: 5 base + hit_cluster
    assert len(encoded.grid) == 6
    assert len(encoded.grid[0]) == 3 and len(encoded.grid[0][0]) == 3
    assert len(encoded.action_mask) == 9
    assert encoded.action_mask.count(0) == 2  # two cells already fired


def test_dqn_selfplay_smoke(tmp_path: Path):
    cfg = TrainConfig(
        output_dir=tmp_path,
        artifact_name="dqn_smoke.npz",
        seed=3,
        device="cpu",
        epochs=1,
        lr=0.001,
        board_size=3,
        version="dqn-test",
        ships=[("Dest", 1), ("Sub", 2)],
    )
    dqn_cfg = DQNSelfCfg(
        gamma=0.9,
        buffer_size=500,
        batch_size=16,
        target_update=50,
        epsilon_start=0.5,
        epsilon_end=0.1,
        epsilon_decay=200,
        lr=0.01,
    )
    sp_cfg = DQNSelfPlayCfg(
        chunk_episodes=50,
        max_rounds=2,
        snapshot_interval=10,
        baseline_games=5,
        baseline_threshold=0.0,
        eval_games=5,
        eval_threshold=0.0,
        loss_penalty=1.0,
    )
    res = run_dqn_selfplay(cfg, dqn_cfg, sp_cfg)
    assert Path(res["artifact"]).exists()

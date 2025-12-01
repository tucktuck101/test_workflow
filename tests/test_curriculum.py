import textwrap
from pathlib import Path

import pytest
import yaml

from training.curriculum import DEFAULT_CURRICULUM_PATH, CurriculumConfig, CurriculumState, load_curriculum


def test_default_curriculum_loads():
    cfg = load_curriculum()
    assert cfg.phases, "default curriculum should define at least one phase"
    assert cfg.phases[0].id == "bootcamp"
    assert cfg.phases[0].gating.min_win_rate == 0.0


def test_custom_curriculum_path(tmp_path: Path):
    curriculum_path = tmp_path / "curriculum.yaml"
    curriculum_path.write_text(
        textwrap.dedent(
            """
            version: v1
            phases:
              - id: phase_one
                name: Phase One
                description: simple start
                gating:
                  min_episodes: 0
                opponents:
                  - opponent: random
                    weight: 1.0
            """
        )
    )
    cfg = load_curriculum(curriculum_path)
    assert cfg.phases[0].id == "phase_one"


def test_invalid_curriculum_rejected(tmp_path: Path):
    bad_curriculum = tmp_path / "bad.yaml"
    bad_curriculum.write_text(
        textwrap.dedent(
            """
            version: v1
            phases:
              - id: bad_phase
                name: Bad
                description: invalid win rate
                gating:
                  min_win_rate: 2.0
                opponents:
                  - opponent: random
                    weight: 1.0
            """
        )
    )
    with pytest.raises(ValueError) as excinfo:
        load_curriculum(bad_curriculum)
    assert "min_win_rate" in str(excinfo.value)


def test_empty_opponent_mix_rejected():
    data = {
        "version": "v1",
        "phases": [
            {
                "id": "lonely",
                "name": "Lonely",
                "description": "missing opponents",
                "gating": {"min_episodes": 0},
                "opponents": [],
            }
        ],
    }
    with pytest.raises(ValueError):
        load_curriculum(data=data)

    data["phases"][0]["opponents"] = [{"opponent": "random", "weight": 0.0}]
    with pytest.raises(ValueError):
        load_curriculum(data=data)


def test_default_path_exists():
    assert DEFAULT_CURRICULUM_PATH.exists()


def _simple_curriculum():
    return CurriculumConfig(
        version="v1",
        phases=[
            {
                "id": "p1",
                "name": "Phase 1",
                "description": "start",
                "gating": {"min_episodes": 1, "min_win_rate": 0.1},
                "opponents": [{"opponent": "random", "weight": 1.0}],
            },
            {
                "id": "p2",
                "name": "Phase 2",
                "description": "complete",
                "gating": {"min_episodes": 0, "min_win_rate": 0.0},
                "opponents": [{"opponent": "random", "weight": 1.0}],
            },
        ],
    )


def test_curriculum_state_transitions_and_persistence(tmp_path: Path):
    curriculum = _simple_curriculum()
    state = CurriculumState(curriculum, tmp_path, run_id="r1")
    state.record_training(1)
    state.record_round(win_rate=0.2, avg_moves=5, baseline_wr=0.5)
    assert state.should_advance() is True
    assert state.advance() is True
    state.persist()
    saved = yaml.safe_load(state.state_path.read_text())
    assert saved["current_phase"] == "p2"
    assert saved["progress"]["episodes"] == 0
    assert saved["total_episodes"] == 1


def test_curriculum_state_limits(tmp_path: Path):
    curriculum = _simple_curriculum()
    state = CurriculumState(curriculum, tmp_path, run_id="r2", max_episodes=2, max_duration_sec=None)
    assert state.limits_reached() is False
    state.record_training(2)
    assert state.limits_reached() is True

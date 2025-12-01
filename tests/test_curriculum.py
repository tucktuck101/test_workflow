import textwrap
from pathlib import Path

import pytest

from training.curriculum import DEFAULT_CURRICULUM_PATH, load_curriculum


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

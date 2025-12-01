from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Any

import yaml


def load_yaml_config(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")
    with p.open() as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("YAML config root must be a mapping")
    return data


def apply_overrides(obj, data: dict[str, Any], key_map: dict[str, str] | None = None) -> None:
    """Apply values from dict to a dataclass object, honoring an optional key map."""
    key_map = key_map or {}
    for f in fields(obj):
        key = key_map.get(f.name, f.name)
        if key in data and data[key] is not None:
            setattr(obj, f.name, data[key])


def validate_yaml_sections(
    cfg: dict[str, Any], required_sections: list[str], allowed_keys: dict[str, set[str]]
) -> None:
    for section in required_sections:
        if section not in cfg or not isinstance(cfg.get(section), dict):
            raise ValueError(f"Missing or invalid section '{section}' in YAML config")
    for section, keys in allowed_keys.items():
        section_data = cfg.get(section, {})
        for k in section_data.keys():
            if k not in keys:
                raise ValueError(f"Unknown key '{k}' in section '{section}'")


def dataclass_field_names(cls) -> set[str]:
    return {f.name for f in fields(cls)}


def expect_type(name: str, val: Any, typ):
    if val is None:
        return
    if not isinstance(val, typ):
        raise ValueError(f"Expected '{name}' to be {typ}, got {type(val)}")


def validate_values(train: Any, dqn: Any, sp: Any) -> None:
    # Train
    if train.board_size <= 0:
        raise ValueError("board_size must be > 0")
    if train.reward_win_decay_k < 0:
        raise ValueError("reward_win_decay_k must be >= 0")
    if train.reward_step_cap > train.reward_step_base:
        raise ValueError("reward_step_cap should be <= reward_step_base")
    # DQN
    if dqn.epsilon_min > dqn.epsilon_start:
        raise ValueError("epsilon_min must be <= epsilon_start")
    if dqn.batch_size <= 0 or dqn.buffer_size <= 0:
        raise ValueError("batch_size and buffer_size must be > 0")
    if dqn.target_update <= 0:
        raise ValueError("target_update must be > 0")
    if len(dqn.conv_channels) != 2:
        raise ValueError("conv_channels must have length 2")
    # Self-play
    if sp.chunk_episodes <= 0:
        raise ValueError("chunk_episodes must be > 0")
    if sp.batch_size <= 0:
        raise ValueError("batch_size must be > 0")
    if sp.rollout_workers <= 0 or sp.eval_workers <= 0 or sp.baseline_workers <= 0:
        raise ValueError("worker counts must be > 0")

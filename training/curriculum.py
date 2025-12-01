from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError, root_validator, validator


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CURRICULUM_PATH = REPO_ROOT / "configs" / "curriculum.default.yaml"


class OpponentMix(BaseModel):
    opponent: str = Field(..., description="opponent type identifier (e.g., random, hunt_target, probability)")
    weight: float = Field(..., gt=0, description="relative probability of sampling this opponent")
    params: Dict[str, object] = Field(default_factory=dict, description="optional opponent-specific parameters")

    @validator("opponent")
    def opponent_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("opponent type cannot be empty")
        return v


class GatingConditions(BaseModel):
    min_episodes: int = Field(0, ge=0, description="minimum number of episodes before evaluating this phase")
    min_rounds: Optional[int] = Field(None, ge=0, description="minimum completed rounds before unlocking")
    min_win_rate: float = Field(0.0, ge=0.0, le=1.0, description="required win rate (0-1) to advance")
    min_avg_moves: Optional[float] = Field(None, gt=0, description="maximum average moves allowed to advance")
    min_baseline_win_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="baseline win rate gate (0-1)")


class TrainOverrides(BaseModel):
    board_size: Optional[int] = Field(None, gt=1)
    allow_adjacent: Optional[bool] = None
    ships: Optional[List[List[object]]] = None
    reward_step_base: Optional[float] = None
    reward_step_decay: Optional[float] = None
    reward_step_cap: Optional[float] = None
    reward_hit: Optional[float] = None
    reward_miss: Optional[float] = None
    reward_sink_mult: Optional[float] = None
    reward_win_max: Optional[float] = None
    reward_win_decay_k: Optional[float] = None
    reward_loss: Optional[float] = None
    reward_perfect_move: Optional[int] = None

    @validator("ships")
    def ships_are_pairs(cls, v: Optional[List[List[object]]]) -> Optional[List[List[object]]]:
        if v is None:
            return v
        for pair in v:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise ValueError("ships entries must be [name, length] pairs")
        return v


class DQNOverrides(BaseModel):
    epsilon_start: Optional[float] = None
    epsilon_end: Optional[float] = None
    epsilon_min: Optional[float] = None
    epsilon_decay: Optional[int] = Field(None, gt=0)
    lr: Optional[float] = Field(None, gt=0)
    gamma: Optional[float] = Field(None, gt=0, le=1)
    batch_size: Optional[int] = Field(None, gt=0)
    buffer_size: Optional[int] = Field(None, gt=0)
    target_update: Optional[int] = Field(None, gt=0)
    warmup_steps: Optional[int] = Field(None, ge=0)
    clip_norm: Optional[float] = Field(None, ge=0)


class SelfPlayOverrides(BaseModel):
    chunk_episodes: Optional[int] = Field(None, gt=0)
    max_rounds: Optional[int] = Field(None, gt=0)
    snapshot_interval: Optional[int] = Field(None, gt=0)
    baseline_games: Optional[int] = Field(None, ge=0)
    baseline_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    eval_games: Optional[int] = Field(None, ge=0)
    eval_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    eval_workers: Optional[int] = Field(None, ge=0)
    rollout_workers: Optional[int] = Field(None, ge=0)
    move_gate: Optional[float] = Field(None, ge=0.0)


class PhaseHyperParams(BaseModel):
    train: Optional[TrainOverrides] = Field(default=None, description="per-phase overrides for TrainConfig")
    dqn: Optional[DQNOverrides] = Field(default=None, description="per-phase overrides for DQNConfig")
    selfplay: Optional[SelfPlayOverrides] = Field(default=None, description="per-phase overrides for SelfPlayConfig")


class CurriculumPhase(BaseModel):
    id: str = Field(..., description="machine readable identifier for the phase")
    name: str = Field(..., description="human readable phase name")
    description: str = Field(..., description="short explanation of the phase goals")
    gating: GatingConditions
    opponents: List[OpponentMix] = Field(default_factory=list, description="opponent mixture for this phase")
    hyperparams: PhaseHyperParams = Field(default_factory=PhaseHyperParams)

    @validator("id", "name", "description")
    def non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("value cannot be empty")
        return v

    @validator("opponents")
    def opponent_weights_positive(cls, v: List[OpponentMix]) -> List[OpponentMix]:
        if not v:
            raise ValueError("at least one opponent mix entry is required")
        total_weight = sum(o.weight for o in v)
        if total_weight <= 0:
            raise ValueError("opponent weights must sum to a positive number")
        return v


class CurriculumConfig(BaseModel):
    version: str = Field("v1", description="schema version identifier")
    phases: List[CurriculumPhase]

    @validator("phases")
    def at_least_one_phase(cls, v: List[CurriculumPhase]) -> List[CurriculumPhase]:
        if not v:
            raise ValueError("at least one curriculum phase is required")
        return v

    @root_validator
    def ensure_unique_ids(cls, values):
        phases: List[CurriculumPhase] = values.get("phases") or []
        seen = set()
        for phase in phases:
            if phase.id in seen:
                raise ValueError(f"duplicate phase id '{phase.id}'")
            seen.add(phase.id)
        return values


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Curriculum file not found: {path}")
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        raise ValueError("Curriculum YAML root must be a mapping")
    return data


def load_curriculum(path: str | Path | None = None, data: dict | None = None) -> CurriculumConfig:
    """
    Load and validate curriculum configuration.
    - If `data` is provided, use it directly.
    - Else if `path` is provided, load the YAML at that path.
    - Else load the default curriculum file.
    """
    if data is not None and path is not None:
        raise ValueError("provide either a curriculum path or data payload, not both")

    if data is None:
        chosen_path = Path(path).expanduser().resolve() if path else DEFAULT_CURRICULUM_PATH
        data = _load_yaml(chosen_path)

    try:
        return CurriculumConfig(**data)
    except ValidationError as exc:
        raise ValueError(f"Invalid curriculum configuration: {exc}") from exc

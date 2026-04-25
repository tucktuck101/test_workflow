from typing import List, Optional

from pydantic import BaseModel, Field

from .engine import PlayerType
from .trainer_orchestrator import RunStatus


class GameConfig(BaseModel):
    player_type: PlayerType = PlayerType.human
    agent_type: PlayerType = PlayerType.dqn_agent
    auto_play: bool = False


class Placement(BaseModel):
    name: str
    coordinates: List[List[int]]


class GameCreateRequest(BaseModel):
    placements: List[Placement] | None = Field(default=None, alias="placements")
    config: GameConfig | None = None

    class Config:
        allow_population_by_field_name = True
        extra = "forbid"


class GameStartResponse(BaseModel):
    game_id: str
    board: List[List[str]]
    agent_board_masked: List[List[str]]
    status: str
    model_version: Optional[str] = None
    model_hash: Optional[str] = None
    player_type: PlayerType = PlayerType.human
    agent_type: PlayerType = PlayerType.dqn_agent
    auto_play: bool = False


class MoveRequest(BaseModel):
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)


class MoveResult(BaseModel):
    outcome: str
    ship: Optional[str] = None


class AgentMove(BaseModel):
    x: int
    y: int
    outcome: str
    ship: Optional[str] = None


class MoveResponse(BaseModel):
    player_result: MoveResult
    agent_move: AgentMove
    board: List[List[str]]
    agent_board_masked: List[List[str]]
    status: str


class QuitResponse(BaseModel):
    status: str


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[dict] = None


class TrainingRunConfig(BaseModel):
    params: dict | None = None


class TrainingRunResponse(BaseModel):
    run_id: str
    status: RunStatus
    config: dict
    error: Optional[str] = None
    created_at: float | None = None
    updated_at: float | None = None


class TrainingMetricsResponse(BaseModel):
    run_id: str
    metrics: dict


class TrainingRunCreateRequest(BaseModel):
    config: dict | None = None


class ModelInfo(BaseModel):
    name: str
    path: str
    hash: str
    size_bytes: int
    modified_at: float
    version: Optional[str] = None


class ModelListResponse(BaseModel):
    active: ModelInfo | None = None
    models: List[ModelInfo]


class ModelLoadRequest(BaseModel):
    name: str
    version: Optional[str] = None
    device: Optional[str] = None

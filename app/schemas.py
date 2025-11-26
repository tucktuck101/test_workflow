from typing import List, Optional

from pydantic import BaseModel, Field


class GameStartResponse(BaseModel):
    game_id: str
    board: List[List[str]]
    agent_board_masked: List[List[str]]
    status: str
    model_version: Optional[str] = None
    model_hash: Optional[str] = None


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

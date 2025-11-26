from typing import List

from fastapi import APIRouter, FastAPI, Request

from . import agent, engine
from .config import Settings
from .errors import raise_http
from .health import readiness_payload
from .model_loader import ModelLoader
from .obs import Observability
from .rate_limit import SimpleRateLimiter
from .schemas import (
    AgentMove,
    ErrorResponse,
    GameStartResponse,
    MoveRequest,
    MoveResponse,
    MoveResult,
    QuitResponse,
)


def _blank_board(size: int) -> List[List[str]]:
    return [["unknown" for _ in range(size)] for _ in range(size)]


def _render_hits(board_size: int, hits: dict) -> List[List[str]]:
    board = _blank_board(board_size)
    for (x, y), outcome in hits.items():
        board[y][x] = outcome.value
    return board


def get_router(app: FastAPI, settings: Settings, loader: ModelLoader, obs: Observability) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["gameplay"])
    session_store = engine.InMemorySessionStore(settings.max_active_games)
    agent_adapter = agent.AgentAdapter(deterministic=settings.deterministic_mode)
    rate_limiter = SimpleRateLimiter(capacity=5, refill_rate_per_sec=1.0, retry_after=5)
    rate_limit_hits = 0

    @router.post(
        "/games",
        response_model=GameStartResponse,
        responses={429: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    )
    def start_game(request: Request):
        client_id = request.client.host if request.client else "anonymous"
        try:
            rate_limiter.allow(client_id)
        except Exception as exc:
            raise_http("rate_limited", {"retry_after": 5})
        if not loader.ready:
            raise_http("model_not_ready")
        with obs.span("game.start"):
            try:
                session = session_store.create(
                    board_size=settings.board_size, deterministic_seed=settings.deterministic_mode and 0 or None
                )
            except engine.InvalidMove:
                raise_http("capacity_exceeded", {"retry_after": 5})

        player_board = _blank_board(settings.board_size)
        agent_board = _blank_board(settings.board_size)
        return GameStartResponse(
            game_id=session.game_id,
            board=player_board,
            agent_board_masked=agent_board,
            status=session.status.value,
            model_version=settings.model_version,
            model_hash=settings.model_hash,
        )

    @router.post(
        "/games/{game_id}/moves",
        response_model=MoveResponse,
        responses={
            400: {"model": ErrorResponse},
            404: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
            429: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def make_move(game_id: str, payload: MoveRequest, request: Request):
        session = session_store.get(game_id)
        if session is None:
            raise_http("game_not_found")

        client_id = request.client.host if request.client else "anonymous"
        try:
            rate_limiter.allow(client_id)
        except Exception:
            raise_http("rate_limited", {"retry_after": 5})

        if not loader.ready:
            raise_http("model_not_ready")
        with obs.span("game.move", {"game_id": session.game_id}):
            try:
                player_result = engine.apply_player_move(session, (payload.x, payload.y))
            except engine.InvalidMove as exc:
                raise_http(str(exc))
            except engine.GameFinished:
                raise_http("game_finished")

            # Agent move (stub/deterministic)
            try:
                loader.assert_ready()
                agent_coord = agent_adapter.next_move(session)
                agent_result = engine.apply_agent_move(session, agent_coord)
            except Exception:
                raise_http("model_not_ready")

        response = MoveResponse(
            player_result=MoveResult(
                outcome=player_result["outcome"], ship=player_result.get("ship")
            ),
            agent_move=AgentMove(
                x=agent_result["x"],
                y=agent_result["y"],
                outcome=agent_result["outcome"],
                ship=agent_result.get("ship"),
            ),
            board=_render_hits(session.board_size, session.player_board_hits),
            agent_board_masked=_render_hits(session.board_size, session.agent_board_hits),
            status=session.status.value,
        )
        return response

    @router.post(
        "/games/{game_id}/quit",
        response_model=QuitResponse,
        responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    )
    def quit_game(game_id: str, request: Request):
        session = session_store.get(game_id)
        if session is None:
            raise_http("game_not_found")
        if session.is_finished():
            raise_http("game_finished")
        engine.quit_game(session)
        session_store.end(game_id)
        return QuitResponse(status="ended")

    return router


def get_health_router(settings: Settings, loader: ModelLoader) -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health/live")
    def live():
        return {"status": "ok"}

    @router.get(
        "/health/ready",
        responses={503: {"model": ErrorResponse}},
    )
    def ready():
        if not loader.ready:
            raise_http("model_not_ready", {"reason": loader.error})
        return readiness_payload(settings)

    return router

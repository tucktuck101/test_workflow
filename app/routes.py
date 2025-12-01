import logging
import random
import time
from typing import Callable, List, Tuple

from fastapi import APIRouter, FastAPI, Request, Body

from bots.scripted_opponents import HuntTargetBot

from . import agent, engine
from .config import Settings
from .errors import raise_http
from .health import readiness_payload
from .model_loader import ModelLoader
from .obs import Observability
from .rate_limit import RateLimitExceeded, SimpleRateLimiter
from .trainer_orchestrator import DummyTrainerOrchestrator, TrainerOrchestrator
from .schemas import (
    AgentMove,
    ErrorResponse,
    GameCreateRequest,
    GameConfig,
    GameStartResponse,
    MoveRequest,
    MoveResponse,
    MoveResult,
    PlayerType,
    QuitResponse,
    TrainingRunCreateRequest,
    TrainingRunResponse,
)

logger = logging.getLogger(__name__)


def _blank_board(size: int) -> List[List[str]]:
    return [["unknown" for _ in range(size)] for _ in range(size)]


def _render_hits(board_size: int, hits: dict) -> List[List[str]]:
    board = _blank_board(board_size)
    for (x, y), outcome in hits.items():
        board[y][x] = outcome.value
    return board


def _render_player_board(session: engine.GameSession) -> List[List[str]]:
    board = _blank_board(session.board_size)
    for ship in session.player_ships:
        for x, y in ship.coordinates:
            board[y][x] = "ship"
    for (x, y), outcome in session.player_board_hits.items():
        board[y][x] = outcome.value
    return board


def _hits_and_misses(board_hits: dict) -> Tuple[set, set]:
    hits = {coord for coord, outcome in board_hits.items() if outcome.value != engine.MoveOutcome.MISS}
    misses = {coord for coord, outcome in board_hits.items() if outcome.value == engine.MoveOutcome.MISS}
    return hits, misses


def _random_unknown(board_hits: dict, board_size: int, seed: int | None) -> Tuple[int, int]:
    hits, misses = _hits_and_misses(board_hits)
    offset_seed = (seed + len(hits) + len(misses)) if seed is not None else None
    rng = random.Random(offset_seed)
    choices = [(x, y) for x in range(board_size) for y in range(board_size) if (x, y) not in hits and (x, y) not in misses]
    if not choices:
        raise engine.InvalidMove("no_available_moves")
    return rng.choice(choices)


def _make_policy(
    player_type: PlayerType,
    role: str,
    board_size: int,
    deterministic_seed: int | None,
    agent_adapter: agent.AgentAdapter,
) -> Callable[[engine.GameSession], Tuple[int, int]]:
    target = "agent" if role == "player" else "player"
    seed = deterministic_seed if deterministic_seed is not None else None
    if player_type == PlayerType.random_bot:
        return lambda session: _random_unknown(
            session.agent_board_hits if target == "agent" else session.player_board_hits, session.board_size, seed
        )
    if player_type == PlayerType.heuristic_bot:
        bot = HuntTargetBot(board_size)

        def _heuristic(session: engine.GameSession) -> Tuple[int, int]:
            hits, misses = _hits_and_misses(session.agent_board_hits if target == "agent" else session.player_board_hits)
            idx = bot.select_action((hits, misses))
            return (idx % session.board_size, idx // session.board_size)

        if deterministic_seed is not None:
            random.seed(deterministic_seed)
        return _heuristic
    if player_type == PlayerType.dqn_agent:
        return lambda session: agent_adapter.next_move(session)
    if player_type == PlayerType.human:
        raise ValueError("human player does not have an automated policy")
    raise ValueError(f"unknown player type {player_type}")


def _auto_play(session: engine.GameSession, player_policy, agent_policy) -> engine.GameSession:
    while not session.is_finished():
        player_move = player_policy(session)
        engine.apply_player_move(session, player_move)
        if session.is_finished():
            break
        agent_move = agent_policy(session)
        engine.apply_agent_move(session, agent_move)
    return session


def get_router(app: FastAPI, settings: Settings, loader: ModelLoader, obs: Observability, trainer_orchestrator: TrainerOrchestrator | None = None) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["gameplay"])
    session_store = engine.InMemorySessionStore(settings.max_active_games, ttl_seconds=3600)
    policy_path = None
    if settings.model_path.exists() and settings.deterministic_mode is False:
        policy_path = settings.model_path
    agent_adapter = agent.AgentAdapter(deterministic=settings.deterministic_mode, policy_path=policy_path)
    trainer_orch = trainer_orchestrator or DummyTrainerOrchestrator()
    rate_limiter = SimpleRateLimiter(capacity=5, refill_rate_per_sec=1.0, retry_after=5)
    rate_limit_hits = 0

    @router.post(
        "/games",
        response_model=GameStartResponse,
        responses={429: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    )
    def start_game(request: Request, payload: GameCreateRequest | None = Body(default=None)) -> GameStartResponse:
        client_id = request.client.host if request.client else "anonymous"
        try:
            rate_limiter.allow(client_id)
        except RateLimitExceeded as exc:
            obs.rate_limit_hits.add(1)
            raise_http("rate_limited", {"retry_after": exc.retry_after}, headers={"Retry-After": str(exc.retry_after)})
        if not loader.ready:
            raise_http("model_not_ready")
        payload = payload or GameCreateRequest()
        config = payload.config or GameConfig()
        if config.agent_type == PlayerType.human:
            raise_http("invalid_payload", {"reason": "agent_type cannot be human"})
        if config.auto_play and (config.player_type == PlayerType.human or config.agent_type == PlayerType.human):
            raise_http("invalid_payload", {"reason": "auto_play requires both players to be bots"})
        with obs.span("game.start"):
            try:
                if payload.placements:
                    ships = [
                        engine.Ship(name=p.name, size=len(p.coordinates), coordinates=[tuple(c) for c in p.coordinates])
                        for p in payload.placements
                    ]
                    engine.validate_placements(settings.board_size, ships)
                    session = engine.create_session_with_player(
                        board_size=settings.board_size,
                        placements=ships,
                        deterministic_seed=settings.deterministic_mode and 0 or None,
                        config=engine.GameConfig(
                            player_type=config.player_type, agent_type=config.agent_type, auto_play=config.auto_play
                        ),
                    )
                    session_store.add(session)
                else:
                    session = session_store.create(
                        board_size=settings.board_size,
                        deterministic_seed=settings.deterministic_mode and 0 or None,
                        config=engine.GameConfig(
                            player_type=config.player_type, agent_type=config.agent_type, auto_play=config.auto_play
                        ),
                    )
            except engine.InvalidMove as exc:
                raise_http(str(exc))

        if config.auto_play:
            try:
                player_policy = _make_policy(config.player_type, "player", settings.board_size, session.deterministic_seed, agent_adapter)
                agent_policy = _make_policy(config.agent_type, "agent", settings.board_size, session.deterministic_seed, agent_adapter)
                session = _auto_play(session, player_policy, agent_policy)
            except Exception as exc:
                session.status = engine.GameStatus.ABORTED
                raise_http("inference_failed", {"reason": str(exc)})

        player_board = _render_player_board(session)
        agent_board = _render_hits(settings.board_size, session.agent_board_hits if config.auto_play else {})
        return GameStartResponse(
            game_id=session.game_id,
            board=player_board,
            agent_board_masked=agent_board,
            status=session.status.value,
            model_version=settings.model_version,
            model_hash=settings.model_hash,
            player_type=config.player_type,
            agent_type=config.agent_type,
            auto_play=config.auto_play,
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
    def make_move(game_id: str, payload: MoveRequest, request: Request) -> MoveResponse:
        session = session_store.get(game_id)
        if session is None:
            raise_http("game_not_found")

        client_id = request.client.host if request.client else "anonymous"
        try:
            rate_limiter.allow(client_id)
        except RateLimitExceeded as exc:
            obs.rate_limit_hits.add(1)
            raise_http("rate_limited", {"retry_after": exc.retry_after}, headers={"Retry-After": str(exc.retry_after)})

        if not loader.ready:
            raise_http("model_not_ready")
        assert session is not None  # for type checker
        with obs.span("game.move", {"game_id": session.game_id}):
            try:
                player_result = engine.apply_player_move(session, (payload.x, payload.y))
            except engine.InvalidMove as exc:
                raise_http(str(exc))
            except engine.GameFinished:
                raise_http("game_finished")

            # Agent move (configurable)
            try:
                infer_start = time.perf_counter()
                if session.config.agent_type == PlayerType.random_bot:
                    agent_coord = _random_unknown(session.player_board_hits, session.board_size, session.deterministic_seed)
                elif session.config.agent_type == PlayerType.heuristic_bot:
                    bot = HuntTargetBot(session.board_size)
                    hits, misses = _hits_and_misses(session.player_board_hits)
                    idx = bot.select_action((hits, misses))
                    agent_coord = (idx % session.board_size, idx // session.board_size)
                else:
                    loader.assert_ready()
                    agent_coord = agent_adapter.next_move(session)
                agent_result = engine.apply_agent_move(session, agent_coord)
                obs.inference_latency.record((time.perf_counter() - infer_start) * 1000)
            except Exception as exc:
                session.status = engine.GameStatus.ABORTED
                raise_http("inference_failed", {"reason": str(exc)})

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
            board=_render_player_board(session),
            agent_board_masked=_render_hits(session.board_size, session.agent_board_hits),
            status=session.status.value,
        )
        return response

    @router.post(
        "/games/{game_id}/quit",
        response_model=QuitResponse,
        responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    )
    def quit_game(game_id: str, request: Request) -> QuitResponse:
        session = session_store.get(game_id)
        if session is None:
            if session_store.was_ended(game_id):
                return QuitResponse(status="ended")
            raise_http("game_not_found")
        assert session is not None
        if not session.is_finished():
            engine.quit_game(session)
        session_store.end(game_id)
        return QuitResponse(status="ended")

    @router.post(
        "/training/runs",
        response_model=TrainingRunResponse,
        responses={503: {"model": ErrorResponse}},
    )
    def start_training(request: Request, payload: TrainingRunCreateRequest | None = Body(default=None)) -> TrainingRunResponse:
        cfg = payload.config if payload else {}
        run = trainer_orch.start_run(cfg or {})
        logger.info("training run requested", extra={"run_id": run.run_id, "client": request.client.host if request.client else "unknown"})
        return TrainingRunResponse(run_id=run.run_id, status=run.status, config=run.config, error=run.error)

    @router.get(
        "/training/runs/{run_id}",
        response_model=TrainingRunResponse,
        responses={404: {"model": ErrorResponse}},
    )
    def get_training(run_id: str) -> TrainingRunResponse:
        run = trainer_orch.get_run(run_id)
        if not run:
            raise_http("training_not_found")
        return TrainingRunResponse(run_id=run.run_id, status=run.status, config=run.config, error=run.error)

    @router.post(
        "/training/runs/{run_id}/cancel",
        response_model=TrainingRunResponse,
        responses={404: {"model": ErrorResponse}},
    )
    def cancel_training(run_id: str) -> TrainingRunResponse:
        run = trainer_orch.cancel_run(run_id)
        if not run:
            raise_http("training_not_found")
        return TrainingRunResponse(run_id=run.run_id, status=run.status, config=run.config, error=run.error)

    return router


def get_health_router(settings: Settings, loader: ModelLoader) -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health/live")
    def live() -> dict:
        return {"status": "ok"}

    @router.get(
        "/health/ready",
        responses={503: {"model": ErrorResponse}},
    )
    def ready() -> dict:
        if not loader.ready:
            raise_http("model_not_ready", {"reason": loader.error})
        return readiness_payload(settings)

    return router

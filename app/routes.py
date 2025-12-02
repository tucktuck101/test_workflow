import logging
import random
import time
from pathlib import Path
from typing import Callable, List, Literal, Tuple

from fastapi import APIRouter, FastAPI, Request

from bots.scripted_opponents import HuntTargetBot

from . import agent, engine
from .config import Settings
from .errors import raise_http
from .health import readiness_payload
from .model_loader import ModelLoader
from .obs import Observability
from .rate_limit import RateLimitExceeded, SimpleRateLimiter
from .schemas import (
    AgentMove,
    ErrorResponse,
    GameConfig,
    GameCreateRequest,
    GameStartResponse,
    MoveRequest,
    MoveResponse,
    MoveResult,
    ModelInfo,
    ModelListResponse,
    ModelLoadRequest,
    PlayerType,
    QuitResponse,
    TrainingMetricsResponse,
    TrainingRunCreateRequest,
    TrainingRunResponse,
)
from .trainer_orchestrator import DummyTrainerOrchestrator, TrainerOrchestrator

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
    hits = {
        coord for coord, outcome in board_hits.items() if outcome.value != engine.MoveOutcome.MISS
    }
    misses = {
        coord for coord, outcome in board_hits.items() if outcome.value == engine.MoveOutcome.MISS
    }
    return hits, misses


def _random_unknown(board_hits: dict, board_size: int, seed: int | None) -> Tuple[int, int]:
    hits, misses = _hits_and_misses(board_hits)
    offset_seed = (seed + len(hits) + len(misses)) if seed is not None else None
    rng = random.Random(offset_seed)
    choices = [
        (x, y)
        for x in range(board_size)
        for y in range(board_size)
        if (x, y) not in hits and (x, y) not in misses
    ]
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
            session.agent_board_hits if target == "agent" else session.player_board_hits,
            session.board_size,
            seed,
        )
    if player_type == PlayerType.heuristic_bot:
        bot = HuntTargetBot(board_size)

        def _heuristic(session: engine.GameSession) -> Tuple[int, int]:
            hits, misses = _hits_and_misses(
                session.agent_board_hits if target == "agent" else session.player_board_hits
            )
            idx = bot.select_action((hits, misses))
            return (idx % session.board_size, idx // session.board_size)

        if deterministic_seed is not None:
            random.seed(deterministic_seed)
        return _heuristic
    if player_type == PlayerType.dqn_agent:
        target_board: Literal["player", "agent"] = "agent" if role == "player" else "player"
        return lambda session: agent_adapter.next_move(session, target=target_board)
    if player_type == PlayerType.human:
        raise ValueError("human player does not have an automated policy")
    raise ValueError(f"unknown player type {player_type}")


def _auto_play(
    session: engine.GameSession,
    player_policy: Callable[[engine.GameSession], Tuple[int, int]],
    agent_policy: Callable[[engine.GameSession], Tuple[int, int]],
) -> engine.GameSession:
    while not session.is_finished():
        try:
            player_move = player_policy(session)
            engine.apply_player_move(session, player_move)
            time.sleep(1.0)
        except engine.InvalidMove:
            # Skip invalid/duplicate moves and continue auto-play.
            continue
        if session.is_finished():
            break
        try:
            agent_move = agent_policy(session)
            engine.apply_agent_move(session, agent_move)
            time.sleep(1.0)
        except engine.InvalidMove:
            continue
    return session


def get_router(
    app: FastAPI,
    settings: Settings,
    loader: ModelLoader,
    obs: Observability,
    trainer_orchestrator: TrainerOrchestrator | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["gameplay"])
    session_store = engine.InMemorySessionStore(settings.max_active_games, ttl_seconds=3600)
    policy_path = None
    if settings.model_path.exists() and settings.deterministic_mode is False:
        policy_path = settings.model_path
    agent_adapter = agent.AgentAdapter(
        deterministic=settings.deterministic_mode, policy_path=policy_path
    )
    trainer_orch: TrainerOrchestrator = trainer_orchestrator or DummyTrainerOrchestrator()
    rate_limiter = SimpleRateLimiter(capacity=5, refill_rate_per_sec=1.0, retry_after=5)

    def _hash_file(path: Path) -> str:
        import hashlib

        hasher = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _list_models() -> List[ModelInfo]:
        models: List[ModelInfo] = []
        root = settings.model_root
        for path in sorted(root.glob("model*.bin")) + sorted(root.glob("*.npz")):
            try:
                digest = _hash_file(path)
            except Exception:
                continue
            info = ModelInfo(
                name=path.name,
                path=str(path),
                hash=digest,
                size_bytes=path.stat().st_size,
                modified_at=path.stat().st_mtime,
                version=path.stem,
            )
            models.append(info)
        return models

    def _active_info() -> ModelInfo:
        p = loader.model_path
        return ModelInfo(
            name=p.name,
            path=str(p),
            hash=loader.expected_hash,
            size_bytes=p.stat().st_size if p.exists() else 0,
            modified_at=p.stat().st_mtime if p.exists() else 0.0,
            version=loader.model_version,
        )

    @router.get("/models", response_model=ModelListResponse)
    def list_models() -> ModelListResponse:
        return ModelListResponse(active=_active_info() if loader.ready else None, models=_list_models())

    @router.get("/models/active", response_model=ModelInfo)
    def active_model() -> ModelInfo:
        if not loader.ready:
            raise_http("model_not_ready", {"reason": loader.error})
        return _active_info()

    @router.post("/models/load", response_model=ModelInfo)
    def load_model(payload: ModelLoadRequest) -> ModelInfo:
        nonlocal agent_adapter
        candidate = settings.model_root / payload.name
        try:
            candidate.resolve().relative_to(settings.model_root.resolve())
        except Exception:
            raise_http("invalid_payload", {"reason": "path_outside_root"})
        if not candidate.exists() or not candidate.is_file():
            raise_http("invalid_payload", {"reason": "model_not_found"})
        digest = _hash_file(candidate)
        version = payload.version or candidate.stem
        device = (payload.device or settings.model_device).lower()
        try:
            loader.load(candidate, version, device)
        except Exception as exc:
            raise_http("invalid_payload", {"reason": str(exc)})
        settings.model_path = candidate
        settings.model_hash = digest
        settings.model_version = version
        settings.model_device = device
        agent_adapter = agent.AgentAdapter(
            deterministic=settings.deterministic_mode, policy_path=candidate
        )
        return _active_info()

    @router.post(
        "/games",
        response_model=GameStartResponse,
        responses={429: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    )
    def start_game(request: Request, payload: GameCreateRequest | None = None) -> GameStartResponse:
        client_id = request.client.host if request.client else "anonymous"
        try:
            rate_limiter.allow(client_id)
        except RateLimitExceeded as exc:
            obs.rate_limit_hits.add(1)
            raise_http(
                "rate_limited",
                {"retry_after": exc.retry_after},
                headers={"Retry-After": str(exc.retry_after)},
            )
        if not loader.ready:
            raise_http("model_not_ready")
        payload = payload or GameCreateRequest()
        config = payload.config or GameConfig()
        if config.agent_type == PlayerType.human:
            raise_http("invalid_payload", {"reason": "agent_type cannot be human"})
        if config.auto_play and (
            config.player_type == PlayerType.human or config.agent_type == PlayerType.human
        ):
            raise_http("invalid_payload", {"reason": "auto_play requires both players to be bots"})
        with obs.span("game.start"):
            try:
                if payload.placements:
                    ships = [
                        engine.Ship(
                            name=p.name,
                            size=len(p.coordinates),
                            coordinates=[(int(c[0]), int(c[1])) for c in p.coordinates],
                        )
                        for p in payload.placements
                    ]
                    engine.validate_placements(settings.board_size, ships)
                    session = engine.create_session_with_player(
                        board_size=settings.board_size,
                        placements=ships,
                        deterministic_seed=settings.deterministic_mode and 0 or None,
                        config=engine.GameConfig(
                            player_type=config.player_type,
                            agent_type=config.agent_type,
                            auto_play=config.auto_play,
                        ),
                    )
                    session_store.add(session)
                else:
                    session = session_store.create(
                        board_size=settings.board_size,
                        deterministic_seed=settings.deterministic_mode and 0 or None,
                        config=engine.GameConfig(
                            player_type=config.player_type,
                            agent_type=config.agent_type,
                            auto_play=config.auto_play,
                        ),
                    )
            except engine.InvalidMove as exc:
                raise_http(str(exc))

        if config.auto_play:
            try:
                player_policy = _make_policy(
                    config.player_type,
                    "player",
                    settings.board_size,
                    session.deterministic_seed,
                    agent_adapter,
                )
                agent_policy = _make_policy(
                    config.agent_type,
                    "agent",
                    settings.board_size,
                    session.deterministic_seed,
                    agent_adapter,
                )
                session = _auto_play(session, player_policy, agent_policy)
            except Exception as exc:
                session.status = engine.GameStatus.ABORTED
                raise_http("inference_failed", {"reason": str(exc)})

        player_board = _render_player_board(session)
        agent_board = _render_hits(
            settings.board_size, session.agent_board_hits if config.auto_play else {}
        )
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
            raise_http(
                "rate_limited",
                {"retry_after": exc.retry_after},
                headers={"Retry-After": str(exc.retry_after)},
            )

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
                    agent_coord = _random_unknown(
                        session.player_board_hits, session.board_size, session.deterministic_seed
                    )
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
    def start_training(
        request: Request, payload: TrainingRunCreateRequest | None = None
    ) -> TrainingRunResponse:
        cfg = payload.config if payload else {}
        run = trainer_orch.start_run(cfg or {})
        logger.info(
            "training run requested",
            extra={
                "run_id": run.run_id,
                "client": request.client.host if request.client else "unknown",
            },
        )
        return TrainingRunResponse(
            run_id=run.run_id,
            status=run.status,
            config=run.config,
            error=run.error,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    @router.get(
        "/training/runs/{run_id}",
        response_model=TrainingRunResponse,
        responses={404: {"model": ErrorResponse}},
    )
    def get_training(run_id: str) -> TrainingRunResponse:
        run = trainer_orch.get_run(run_id)
        if not run:
            raise_http("training_not_found")
        assert run is not None
        return TrainingRunResponse(
            run_id=run.run_id,
            status=run.status,
            config=run.config,
            error=run.error,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    @router.post(
        "/training/runs/{run_id}/cancel",
        response_model=TrainingRunResponse,
        responses={404: {"model": ErrorResponse}},
    )
    def cancel_training(run_id: str) -> TrainingRunResponse:
        run = trainer_orch.cancel_run(run_id)
        if not run:
            raise_http("training_not_found")
        assert run is not None
        return TrainingRunResponse(
            run_id=run.run_id,
            status=run.status,
            config=run.config,
            error=run.error,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    @router.get(
        "/training/runs/{run_id}/metrics",
        response_model=TrainingMetricsResponse,
        responses={404: {"model": ErrorResponse}},
    )
    def training_metrics(run_id: str) -> TrainingMetricsResponse:
        metrics = trainer_orch.get_metrics(run_id)
        if metrics is None:
            raise_http("training_not_found")
        assert metrics is not None
        return TrainingMetricsResponse(run_id=run_id, metrics=metrics)

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
        return readiness_payload(settings, loader)

    return router

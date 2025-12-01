import enum
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

Coordinate = Tuple[int, int]


class GameStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    PLAYER_WON = "player_won"
    AGENT_WON = "agent_won"
    QUIT = "quit"
    ABORTED = "aborted"


class PlayerType(str, enum.Enum):
    HUMAN = "human"
    RANDOM_BOT = "random_bot"
    HEURISTIC_BOT = "heuristic_bot"
    DQN_AGENT = "dqn_agent"


@dataclass
class GameConfig:
    player_type: PlayerType = PlayerType.HUMAN
    agent_type: PlayerType = PlayerType.DQN_AGENT
    auto_play: bool = False


class MoveOutcome(str, enum.Enum):
    MISS = "miss"
    HIT = "hit"
    SUNK = "sunk"


class InvalidMove(ValueError):
    """Raised when a move is invalid (bounds, duplicate, or finished game)."""


class GameFinished(ValueError):
    """Raised when a move is attempted on a finished game."""


@dataclass
class Ship:
    name: str
    size: int
    coordinates: List[Coordinate] = field(default_factory=list)
    hits: List[Coordinate] = field(default_factory=list)

    @property
    def is_sunk(self) -> bool:
        return len(self.hits) == self.size

    def register_hit(self, coord: Coordinate) -> MoveOutcome:
        if coord not in self.coordinates:
            return MoveOutcome.MISS
        if coord not in self.hits:
            self.hits.append(coord)
        return MoveOutcome.SUNK if self.is_sunk else MoveOutcome.HIT


@dataclass
class GameSession:
    game_id: str
    board_size: int
    player_ships: List[Ship]
    agent_ships: List[Ship]
    player_board_hits: Dict[Coordinate, MoveOutcome] = field(default_factory=dict)
    agent_board_hits: Dict[Coordinate, MoveOutcome] = field(default_factory=dict)
    move_history: List[Dict] = field(default_factory=list)
    status: GameStatus = GameStatus.IN_PROGRESS
    deterministic_seed: Optional[int] = None
    config: GameConfig = field(default_factory=GameConfig)

    def is_finished(self) -> bool:
        return self.status != GameStatus.IN_PROGRESS


SHIP_SET = [
    ("Carrier", 5),
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Submarine", 3),
    ("Destroyer", 2),
]


def _neighbors(coord: Coordinate) -> List[Coordinate]:
    x, y = coord
    return [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if not (dx == 0 and dy == 0)]


def _place_ships(board_size: int, rng: random.Random, *, allow_adjacent: bool = True) -> List[Ship]:
    occupied = set()
    ships: List[Ship] = []

    for name, size in SHIP_SET:
        placed = False
        while not placed:
            vertical = rng.choice([True, False])
            if vertical:
                x = rng.randint(0, board_size - 1)
                y = rng.randint(0, board_size - size)
                coords = [(x, y + i) for i in range(size)]
            else:
                x = rng.randint(0, board_size - size)
                y = rng.randint(0, board_size - 1)
                coords = [(x + i, y) for i in range(size)]
            if any(c in occupied for c in coords):
                continue
            if not allow_adjacent and any(n in occupied for coord in coords for n in _neighbors(coord)):
                continue
            occupied.update(coords)
            ships.append(Ship(name=name, size=size, coordinates=coords))
            placed = True
    return ships


def _check_bounds(board_size: int, coord: Coordinate) -> None:
    x, y = coord
    if x < 0 or y < 0 or x >= board_size or y >= board_size:
        raise InvalidMove("invalid_coordinates")


def _check_linearity(size: int, coords: List[Coordinate]) -> None:
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    same_x = len(set(xs)) == 1
    same_y = len(set(ys)) == 1
    if not (same_x or same_y):
        raise InvalidMove("invalid_coordinates")
    if same_x:
        ordered = sorted(ys)
        if ordered != list(range(min(ys), min(ys) + size)):
            raise InvalidMove("invalid_coordinates")
    else:
        ordered = sorted(xs)
        if ordered != list(range(min(xs), min(xs) + size)):
            raise InvalidMove("invalid_coordinates")


def validate_placements(board_size: int, placements: List[Ship], *, allow_adjacent: bool = True) -> None:
    occupied = set()
    expected = {name: size for name, size in SHIP_SET}
    if len(placements) != len(expected):
        raise InvalidMove("invalid_coordinates")
    seen = set()
    for ship in placements:
        if ship.name not in expected or ship.name in seen:
            raise InvalidMove("invalid_coordinates")
        seen.add(ship.name)
        expected_size = expected[ship.name]
        if len(ship.coordinates) != expected_size:
            raise InvalidMove("invalid_coordinates")
        _check_linearity(expected_size, ship.coordinates)
        for coord in ship.coordinates:
            _check_bounds(board_size, coord)
            if coord in occupied:
                raise InvalidMove("duplicate_move")
            if not allow_adjacent and any(n in occupied for n in _neighbors(coord)):
                raise InvalidMove("duplicate_move")
            occupied.add(coord)
    if seen != set(expected.keys()):
        raise InvalidMove("invalid_coordinates")


def create_session(board_size: int, deterministic_seed: Optional[int] = None, config: GameConfig | None = None) -> GameSession:
    rng = random.Random(deterministic_seed)
    player_ships = _place_ships(board_size, rng)
    agent_ships = _place_ships(board_size, rng)
    return GameSession(
        game_id=str(uuid.uuid4()),
        board_size=board_size,
        player_ships=player_ships,
        agent_ships=agent_ships,
        deterministic_seed=deterministic_seed,
        config=config or GameConfig(),
    )


def create_session_with_player(board_size: int, placements: List[Ship], deterministic_seed: Optional[int] = None, config: GameConfig | None = None) -> GameSession:
    rng = random.Random(deterministic_seed)
    agent_ships = _place_ships(board_size, rng)
    return GameSession(
        game_id=str(uuid.uuid4()),
        board_size=board_size,
        player_ships=placements,
        agent_ships=agent_ships,
        deterministic_seed=deterministic_seed,
        config=config or GameConfig(),
    )


def _find_ship(ships: List[Ship], coord: Coordinate) -> Optional[Ship]:
    for ship in ships:
        if coord in ship.coordinates:
            return ship
    return None


def _register_move(
    session: GameSession,
    actor: str,
    target_ships: List[Ship],
    board_hits: Dict[Coordinate, MoveOutcome],
    coord: Coordinate,
) -> Dict:
    if session.is_finished():
        raise GameFinished("game_finished")
    _check_bounds(session.board_size, coord)
    if coord in board_hits:
        raise InvalidMove("duplicate_move")

    ship = _find_ship(target_ships, coord)
    if ship:
        outcome = ship.register_hit(coord)
    else:
        outcome = MoveOutcome.MISS

    board_hits[coord] = outcome
    move_record = {"actor": actor, "x": coord[0], "y": coord[1], "outcome": outcome.value}
    if ship and outcome != MoveOutcome.MISS:
        move_record["ship"] = ship.name
    session.move_history.append(move_record)
    return move_record


def apply_player_move(session: GameSession, coord: Coordinate) -> Dict:
    """Apply a player move against the agent's board."""
    result = _register_move(session, "player", session.agent_ships, session.agent_board_hits, coord)
    if all(ship.is_sunk for ship in session.agent_ships):
        session.status = GameStatus.PLAYER_WON
    return result


def apply_agent_move(session: GameSession, coord: Coordinate) -> Dict:
    """Apply an agent move against the player's board."""
    result = _register_move(session, "agent", session.player_ships, session.player_board_hits, coord)
    if all(ship.is_sunk for ship in session.player_ships):
        session.status = GameStatus.AGENT_WON
    return result


def quit_game(session: GameSession) -> None:
    session.status = GameStatus.QUIT


class InMemorySessionStore:
    """Soft-cap in-memory session store with TTL support."""

    def __init__(self, max_active_games: Optional[int] = None, ttl_seconds: Optional[int] = None) -> None:
        self._sessions: Dict[str, GameSession] = {}
        self._ended_ids: set[str] = set()
        self._max = max_active_games
        self._ttl = ttl_seconds
        self._created_at: Dict[str, float] = {}

    def create(self, board_size: int, deterministic_seed: Optional[int] = None, config: GameConfig | None = None) -> GameSession:
        if self._max is not None and len(self._sessions) >= self._max:
            raise InvalidMove("capacity_exceeded")
        session = create_session(board_size, deterministic_seed, config=config)
        self._sessions[session.game_id] = session
        self._created_at[session.game_id] = time.time()
        return session

    def add(self, session: GameSession) -> None:
        if self._max is not None and len(self._sessions) >= self._max:
            raise InvalidMove("capacity_exceeded")
        self._sessions[session.game_id] = session
        self._created_at[session.game_id] = time.time()

    def get(self, game_id: str) -> Optional[GameSession]:
        session = self._sessions.get(game_id)
        if session and self._ttl is not None:
            created = self._created_at.get(game_id, 0)
            if time.time() - created > self._ttl:
                self.end(game_id)
                return None
        return session

    def end(self, game_id: str) -> None:
        self._sessions.pop(game_id, None)
        self._ended_ids.add(game_id)
        self._created_at.pop(game_id, None)

    @property
    def active_count(self) -> int:
        return len(self._sessions)

    def was_ended(self, game_id: str) -> bool:
        return game_id in self._ended_ids

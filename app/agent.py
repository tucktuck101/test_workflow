import random
from typing import Optional, Tuple

from .engine import GameSession, InvalidMove, _check_bounds

Coordinate = Tuple[int, int]


class AgentAdapter:
    """Simple deterministic-capable agent for MVP; replace with real model later."""

    def __init__(self, deterministic: bool = False) -> None:
        self._deterministic = deterministic

    def next_move(self, session: GameSession) -> Coordinate:
        rng = random.Random(session.deterministic_seed if self._deterministic else None)
        tried = set(session.player_board_hits.keys())
        # naive scan first, then fallback to random available
        for x in range(session.board_size):
            for y in range(session.board_size):
                if (x, y) not in tried:
                    return (x, y)
        available = [
            (x, y)
            for x in range(session.board_size)
            for y in range(session.board_size)
            if (x, y) not in tried
        ]
        if not available:
            raise InvalidMove("no_available_moves")
        return rng.choice(available)

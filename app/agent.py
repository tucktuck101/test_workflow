import json
import random
from pathlib import Path
from typing import Dict, Optional, Tuple

from .engine import GameSession, InvalidMove, _check_bounds

Coordinate = Tuple[int, int]


class AgentAdapter:
    """Agent that can operate in deterministic or learned policy mode."""

    def __init__(self, deterministic: bool = False, policy_path: Optional[Path] = None) -> None:
        self._deterministic = deterministic
        self._policy: Dict[Coordinate, float] = {}
        if policy_path:
            self._policy = self._load_policy(policy_path)

    def _load_policy(self, path: Path) -> Dict[Coordinate, float]:
        try:
            data = json.loads(path.read_text())
            policy: Dict[Coordinate, float] = {}
            for key, value in data.items():
                x, y = key.split(",")
                policy[(int(x), int(y))] = float(value)
            return policy
        except Exception:
            # If not a JSON policy (e.g., stub binary), fall back to scan/random.
            return {}

    def next_move(self, session: GameSession) -> Coordinate:
        tried = set(session.player_board_hits.keys())
        actions = [
            (x, y)
            for x in range(session.board_size)
            for y in range(session.board_size)
            if (x, y) not in tried
        ]
        if not actions:
            raise InvalidMove("no_available_moves")

        if self._policy:
            # greedy over learned Q-values
            best = max(actions, key=lambda a: self._policy.get(a, 0.0))
            return best

        rng = random.Random(session.deterministic_seed if self._deterministic else None)
        # naive scan first, then fallback to random available
        for x in range(session.board_size):
            for y in range(session.board_size):
                if (x, y) not in tried:
                    return (x, y)
        return rng.choice(actions)

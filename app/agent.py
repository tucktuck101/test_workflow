import json
import random
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple

import numpy as np

from training.env import BattleshipEnv
from training.state_encoder import encode_state

from .engine import SHIP_SET, GameSession, InvalidMove

Coordinate = Tuple[int, int]


class AgentAdapter:
    """Agent that can operate in deterministic or learned policy mode."""

    def __init__(self, deterministic: bool = False, policy_path: Optional[Path] = None) -> None:
        self._deterministic = deterministic
        self._policy: Dict[Coordinate, float] = {}
        self._dqn: Optional[dict] = None
        if policy_path:
            if policy_path.suffix == ".npz":
                self._load_dqn(policy_path)
            else:
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

    def _load_dqn(self, path: Path) -> None:
        try:
            data = np.load(path, allow_pickle=True)
            self._dqn = {k: data[k] for k in data.files}
        except Exception:
            self._dqn = None

    def _encode_session_state(self, session: GameSession) -> Tuple[np.ndarray, List[int]]:
        # Build hits/misses from player's perspective (shots on agent)
        hits = {
            coord for coord, outcome in session.agent_board_hits.items() if outcome.value != "miss"
        }
        misses = {
            coord for coord, outcome in session.agent_board_hits.items() if outcome.value == "miss"
        }
        last_player_shot = None
        last_agent_shot = None
        for move in reversed(session.move_history):
            if move["actor"] == "player" and last_player_shot is None:
                last_player_shot = (move["x"], move["y"])
            if move["actor"] == "agent" and last_agent_shot is None:
                last_agent_shot = (move["x"], move["y"])
            if last_player_shot and last_agent_shot:
                break
        total_ship_cells = sum(size for _, size in SHIP_SET)
        remaining = max(total_ship_cells - len(hits), 1)
        dummy_env = BattleshipEnv(board_size=session.board_size, ships=list(SHIP_SET))
        dummy_env.moves_taken = len(session.move_history)
        dummy_env.max_moves = session.board_size * session.board_size
        encoded = encode_state(
            dummy_env,
            last_player_shot=last_player_shot,
            last_agent_shot=last_agent_shot,
            include_hit_cluster=True,
            hits_override=hits,
            misses_override=misses,
            remaining_override=remaining,
            max_moves_override=dummy_env.max_moves,
        )
        grid = np.array(encoded.grid, dtype=np.float32)
        return grid, encoded.action_mask

    def _dqn_forward(
        self, grid: np.ndarray, weights: dict, mask: List[int], board_size: int
    ) -> Coordinate:
        x = grid.reshape(1, -1)
        w1, b1 = weights["w1"], weights["b1"]
        w2, b2 = weights["w2"], weights["b2"]
        h1 = np.maximum(0, x @ w1 + b1)
        h2 = np.maximum(0, h1 @ w2 + b2)
        if weights.get("use_dueling"):
            wv, bv = weights["wv"], weights["bv"]
            wa, ba = weights["wa"], weights["ba"]
            v = h2 @ wv + bv
            a = h2 @ wa + ba
            q = v + (a - np.mean(a, axis=1, keepdims=True))
        else:
            w3, b3 = weights["w3"], weights["b3"]
            q = h2 @ w3 + b3
        q = q.reshape(-1)
        mask_arr = np.array(mask, dtype=bool)
        q = np.where(mask_arr, q, -1e9)
        idx = int(np.argmax(q))
        return (idx % board_size, idx // board_size)

    def next_move(
        self, session: GameSession, target: Literal["player", "agent"] = "player"
    ) -> Coordinate:
        tried = (
            set(session.agent_board_hits.keys())
            if target == "agent"
            else set(session.player_board_hits.keys())
        )
        actions = [
            (x, y)
            for x in range(session.board_size)
            for y in range(session.board_size)
            if (x, y) not in tried
        ]
        if not actions:
            raise InvalidMove("no_available_moves")

        if self._dqn is not None:
            grid, mask = self._encode_session_state(session)
            try:
                return self._dqn_forward(grid, self._dqn, mask, session.board_size)
            except Exception:
                pass

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

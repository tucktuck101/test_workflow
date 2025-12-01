import numpy as np
from typing import List, Tuple

Coordinate = Tuple[int, int]


def _neighbors(coord: Coordinate):
    x, y = coord
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        yield x + dx, y + dy


class VectorEnv:
    """Vectorized Battleship environment for faster training (single agent vs static board)."""

    def __init__(
        self,
        board_size: int = 10,
        seed: int = 0,
        ships: List[Tuple[str, int]] | None = None,
        allow_adjacent: bool = True,
        reward_step_base: float = -0.05,
        reward_step_decay: float = 0.0,
        reward_step_cap: float = -0.5,
        reward_hit: float = 1.0,
        reward_miss: float = 0.0,
        reward_sink_mult: float = 1.0,
        reward_win_max: float = 5.0,
        reward_win_decay_k: float = 82.0,
        reward_loss: float = -10.0,
        reward_perfect_move: int = 17,
        duplicate_penalty: float = 0.5,
    ):
        self.board_size = board_size
        self.seed = seed
        self.ships = ships or [("Carrier", 5), ("Battleship", 4), ("Cruiser", 3), ("Submarine", 3), ("Destroyer", 2)]
        self.allow_adjacent = allow_adjacent
        self.rng = np.random.default_rng(seed)
        self.max_moves = board_size * board_size
        self.reward_step_base = reward_step_base
        self.reward_step_decay = reward_step_decay
        self.reward_step_cap = reward_step_cap
        self.reward_hit = reward_hit
        self.reward_miss = reward_miss
        self.reward_sink_mult = reward_sink_mult
        self.reward_win_max = reward_win_max
        self.reward_win_decay_k = reward_win_decay_k
        self.reward_loss = reward_loss
        self.reward_perfect_move = reward_perfect_move
        self.duplicate_penalty = duplicate_penalty
        self.reset()

    def reset(self) -> None:
        self.hits = np.zeros((self.board_size, self.board_size), dtype=bool)
        self.misses = np.zeros((self.board_size, self.board_size), dtype=bool)
        self.agent_board, self.ship_id, self.ship_sizes = self._place_ships()
        self.ship_remaining = self.ship_sizes.copy()
        self.remaining = int(self.agent_board.sum())
        self.moves_taken = 0

    def _place_ships(self) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        board = np.zeros((self.board_size, self.board_size), dtype=bool)
        ship_id = np.zeros((self.board_size, self.board_size), dtype=np.int32)
        ship_sizes: List[int] = []
        for ship_idx, (_, size) in enumerate(self.ships, start=1):
            placed = False
            attempts = 0
            while not placed:
                attempts += 1
                if attempts > 5000:
                    raise ValueError("Failed to place ships with current constraints; enlarge board or allow adjacency.")
                vertical = self.rng.integers(0, 2) == 1
                if vertical:
                    x = self.rng.integers(0, self.board_size)
                    y = self.rng.integers(0, self.board_size - size + 1)
                    coords = [(x, y + i) for i in range(size)]
                else:
                    x = self.rng.integers(0, self.board_size - size + 1)
                    y = self.rng.integers(0, self.board_size)
                    coords = [(x + i, y) for i in range(size)]
                if any(board[cy, cx] for cx, cy in coords):
                    continue
                if not self.allow_adjacent:
                    bad = False
                    for cx, cy in coords:
                        for nx, ny in _neighbors((cx, cy)):
                            if 0 <= nx < self.board_size and 0 <= ny < self.board_size and board[ny, nx]:
                                bad = True
                                break
                        if bad:
                            break
                    if bad:
                        continue
                for cx, cy in coords:
                    board[cy, cx] = True
                    ship_id[cy, cx] = ship_idx
                placed = True
            ship_sizes.append(size)
        return board, ship_id, ship_sizes

    def _step_penalty(self, move_idx: int) -> float:
        penalty = self.reward_step_base
        if move_idx > self.reward_perfect_move:
            penalty -= self.reward_step_decay * (move_idx - self.reward_perfect_move)
        penalty = max(penalty, self.reward_step_cap)
        return penalty

    def step(self, action: Coordinate) -> tuple[float, bool]:
        x, y = action
        self.moves_taken += 1
        reward = self._step_penalty(self.moves_taken)
        done = False
        if self.hits[y, x] or self.misses[y, x]:
            reward -= self.duplicate_penalty
        elif self.agent_board[y, x]:
            self.hits[y, x] = True
            self.remaining -= 1
            reward += self.reward_hit
            ship_idx = int(self.ship_id[y, x])
            sunk_len = 0
            if ship_idx > 0:
                self.ship_remaining[ship_idx - 1] -= 1
                if self.ship_remaining[ship_idx - 1] == 0:
                    sunk_len = self.ship_sizes[ship_idx - 1]
                    reward += self.reward_sink_mult * sunk_len
            if self.remaining == 0:
                decay = 0.0
                if self.reward_win_decay_k > 0:
                    decay = max(0.0, 1 - max(0, self.moves_taken - self.reward_perfect_move) / self.reward_win_decay_k)
                reward += self.reward_win_max * decay
                done = True
        else:
            self.misses[y, x] = True
            reward += self.reward_miss
        if self.moves_taken >= self.max_moves:
            done = True
        if done and self.remaining > 0:
            reward += self.reward_loss
        return reward, done

    def clone_params(self):
        return {
            "board_size": self.board_size,
            "ships": self.ships,
            "allow_adjacent": self.allow_adjacent,
            "reward_step_base": self.reward_step_base,
            "reward_step_decay": self.reward_step_decay,
            "reward_step_cap": self.reward_step_cap,
            "reward_hit": self.reward_hit,
            "reward_miss": self.reward_miss,
            "reward_sink_mult": self.reward_sink_mult,
            "reward_win_max": self.reward_win_max,
            "reward_win_decay_k": self.reward_win_decay_k,
            "reward_loss": self.reward_loss,
            "reward_perfect_move": self.reward_perfect_move,
            "duplicate_penalty": self.duplicate_penalty,
        }


class BatchedEnv:
    """Batch N environments together for parallel stepping on CPU."""

    def __init__(self, batch_size: int, params: dict, seed: int = 0):
        self.batch_size = batch_size
        self.params = params
        self.seed = seed
        self.envs = [VectorEnv(seed=seed + i, **params) for i in range(batch_size)]

    def reset(self):
        for env in self.envs:
            env.reset()

    def step(self, actions: List[Coordinate]) -> tuple[List[float], List[bool]]:
        rewards = []
        dones = []
        for env, action in zip(self.envs, actions):
            r, d = env.step(action)
            rewards.append(r)
            dones.append(d)
        return rewards, dones

    def get_states(self):
        return [(env.hits, env.misses, env.moves_taken, env.max_moves) for env in self.envs]

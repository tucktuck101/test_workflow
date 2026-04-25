import random
from dataclasses import dataclass, field
from typing import List, Tuple

Coordinate = Tuple[int, int]
DEFAULT_SHIPS: List[Tuple[str, int]] = [
    ("Carrier", 5),
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Submarine", 3),
    ("Destroyer", 2),
]


@dataclass
class BattleshipEnv:
    board_size: int = 10
    seed: int = 0
    ships: List[Tuple[str, int]] = field(default_factory=lambda: list(DEFAULT_SHIPS))
    max_moves: int = 0
    allow_adjacent: bool = True
    reward_step_base: float = -0.05
    reward_step_decay: float = 0.0
    reward_step_cap: float = -0.5
    reward_hit: float = 1.0
    reward_miss: float = 0.0
    reward_sink_mult: float = 1.0
    reward_win_max: float = 5.0
    reward_win_decay_k: float = 82.0
    reward_loss: float = -10.0
    reward_perfect_move: int = 17
    duplicate_penalty: float = 0.1

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)
        max_ship = max(size for _, size in self.ships)
        if self.board_size < max_ship:
            raise ValueError(f"board_size {self.board_size} too small for ship of size {max_ship}")
        if self.max_moves <= 0:
            self.max_moves = self.board_size * self.board_size
        self.reset()

    def reset(self) -> None:
        self.agent_board, self.ship_cells, self.cell_to_ship = self._place_ships()
        self.ship_remaining = [len(cells) for cells in self.ship_cells]
        self.hits: set[Coordinate] = set()
        self.misses: set[Coordinate] = set()
        self.remaining = sum(size for _, size in self.ships)
        self.moves_taken = 0

    def _neighbors(self, coord: Coordinate) -> List[Coordinate]:
        x, y = coord
        return [
            (x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if not (dx == 0 and dy == 0)
        ]

    def _place_ships(self) -> Tuple[List[Coordinate], List[set], dict]:
        coords: List[Coordinate] = []
        occupied = set()
        ship_cells: List[set] = []
        cell_to_ship: dict = {}
        for _, size in self.ships:
            placed = False
            attempts = 0
            while not placed:
                attempts += 1
                if attempts > 5000:
                    raise ValueError(
                        "Failed to place ships with current constraints; try a larger board or allow adjacency."
                    )
                vertical = self.rng.choice([True, False])
                if vertical:
                    x = self.rng.randint(0, self.board_size - 1)
                    y = self.rng.randint(0, self.board_size - size)
                    ship_coords = [(x, y + i) for i in range(size)]
                else:
                    x = self.rng.randint(0, self.board_size - size)
                    y = self.rng.randint(0, self.board_size - 1)
                    ship_coords = [(x + i, y) for i in range(size)]
                if any(c in occupied for c in ship_coords):
                    continue
                if not self.allow_adjacent and any(
                    n in occupied for coord in ship_coords for n in self._neighbors(coord)
                ):
                    continue
                coords.extend(ship_coords)
                occupied.update(ship_coords)
                ship_idx = len(ship_cells)
                ship_cells.append(set(ship_coords))
                for cell in ship_coords:
                    cell_to_ship[cell] = ship_idx
                placed = True
        return coords, ship_cells, cell_to_ship

    def _step_penalty(self, move_idx: int) -> float:
        penalty = self.reward_step_base
        if move_idx > self.reward_perfect_move:
            penalty -= self.reward_step_decay * (move_idx - self.reward_perfect_move)
        penalty = max(penalty, self.reward_step_cap)
        return penalty

    def step(self, action: Coordinate) -> Tuple[float, bool]:
        """Apply an action (fire at coordinate). Returns reward, done."""
        self.moves_taken += 1
        reward = self._step_penalty(self.moves_taken)
        done = False

        if action in self.hits or action in self.misses:
            # duplicate shot penalty
            reward -= self.duplicate_penalty
        elif action in self.agent_board:
            self.hits.add(action)
            self.remaining -= 1
            reward += self.reward_hit
            sunk_len = 0
            ship_idx = self.cell_to_ship.get(action)
            if ship_idx is not None:
                self.ship_remaining[ship_idx] -= 1
                if self.ship_remaining[ship_idx] == 0:
                    sunk_len = len(self.ship_cells[ship_idx])
                    reward += self.reward_sink_mult * sunk_len
            if self.remaining == 0:
                decay = 0.0
                if self.reward_win_decay_k > 0:
                    decay = max(
                        0.0,
                        1
                        - max(0, self.moves_taken - self.reward_perfect_move)
                        / self.reward_win_decay_k,
                    )
                reward += self.reward_win_max * decay
                done = True
        else:
            self.misses.add(action)
            reward += self.reward_miss

        if self.moves_taken >= self.max_moves:
            done = True
        if done and self.remaining > 0:
            reward += self.reward_loss

        return reward, done

    def available_actions(self) -> List[Coordinate]:
        actions = []
        for x in range(self.board_size):
            for y in range(self.board_size):
                if (x, y) not in self.hits and (x, y) not in self.misses:
                    actions.append((x, y))
        return actions

    def state_vector(self) -> List[int]:
        # encode board as 0 unknown, 1 hit, -1 miss
        vec: List[int] = []
        for y in range(self.board_size):
            for x in range(self.board_size):
                coord = (x, y)
                if coord in self.hits:
                    vec.append(1)
                elif coord in self.misses:
                    vec.append(-1)
                else:
                    vec.append(0)
        return vec

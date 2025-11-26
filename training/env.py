import random
from dataclasses import dataclass, field
from typing import List, Tuple

Coordinate = Tuple[int, int]


@dataclass
class BattleshipEnv:
    board_size: int = 5
    seed: int = 0
    ships: List[Tuple[str, int]] = field(
        default_factory=lambda: [
            ("Destroyer", 2),
            ("Submarine", 3),
        ]
    )
    max_moves: int = 50

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)
        self.reset()

    def reset(self) -> None:
        self.agent_board = self._place_ships()
        self.hits = set()
        self.misses = set()
        self.remaining = sum(size for _, size in self.ships)
        self.moves_taken = 0

    def _place_ships(self) -> List[Coordinate]:
        coords: List[Coordinate] = []
        occupied = set()
        for _, size in self.ships:
            placed = False
            while not placed:
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
                coords.extend(ship_coords)
                occupied.update(ship_coords)
                placed = True
        return coords

    def step(self, action: Coordinate) -> Tuple[float, bool]:
        """Apply an action (fire at coordinate). Returns reward, done."""
        self.moves_taken += 1
        reward = -0.05  # small step penalty to encourage efficiency
        done = False

        if action in self.hits or action in self.misses:
            # duplicate shot penalty
            reward -= 0.1
        elif action in self.agent_board:
            self.hits.add(action)
            self.remaining -= 1
            reward += 1.0
            if self.remaining == 0:
                reward += 5.0
                done = True
        else:
            self.misses.add(action)

        if self.moves_taken >= self.max_moves:
            done = True

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

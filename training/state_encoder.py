from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from .env import BattleshipEnv, Coordinate

# Channel order (when include_self=False and no extras):
# 0: agent_unknown, 1: agent_miss, 2: agent_hit, 3: last_player_shot, 4: last_agent_shot
DEFAULT_CHANNEL_NAMES = [
    "agent_unknown",
    "agent_miss",
    "agent_hit",
    "last_player_shot",
    "last_agent_shot",
]


@dataclass
class EncodedState:
    grid: List[List[List[float]]]  # shape [channels][H][W]
    action_mask: List[int]  # length H*W, 1 for legal moves (unshot), 0 otherwise
    scalars: List[float]  # normalized global features
    channel_names: List[str]


def _empty_grid(channels: int, size: int) -> List[List[List[float]]]:
    return [[[0.0 for _ in range(size)] for _ in range(size)] for _ in range(channels)]


def _neighbors(coord: Coordinate) -> Iterable[Coordinate]:
    x, y = coord
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        yield x + dx, y + dy


def encode_state(
    env: BattleshipEnv,
    last_player_shot: Optional[Coordinate] = None,
    last_agent_shot: Optional[Coordinate] = None,
    include_self: bool = False,
    include_hit_cluster: bool = False,
    hits_override: Optional[set[Coordinate]] = None,
    misses_override: Optional[set[Coordinate]] = None,
    remaining_override: Optional[int] = None,
    max_moves_override: Optional[int] = None,
) -> EncodedState:
    """
    Encode the current environment into channels suitable for a DQN.

    Channels (always present):
      - agent_unknown, agent_miss, agent_hit
      - last_player_shot (one-hot)
      - last_agent_shot (one-hot)

    Optional channels:
      - self_unknown, self_hit (if include_self=True)
      - hit_cluster (adjacent to known hits) if include_hit_cluster=True

    Scalars:
      - move_fraction (moves_taken / max_moves)
      - remaining_fraction (remaining ship cells / total ship cells)
    """
    channel_names: List[str] = list(DEFAULT_CHANNEL_NAMES)
    if include_self:
        channel_names.extend(["self_unknown", "self_hit"])
    if include_hit_cluster:
        channel_names.append("hit_cluster")

    size = env.board_size
    grid = _empty_grid(len(channel_names), size)

    total_ship_cells = sum(size for _, size in env.ships)
    remaining = remaining_override if remaining_override is not None else env.remaining
    remaining_fraction = remaining / total_ship_cells if total_ship_cells else 0.0
    moves_taken = env.moves_taken
    max_moves = max_moves_override if max_moves_override is not None else env.max_moves
    move_fraction = moves_taken / max_moves if max_moves else 0.0

    hits = hits_override if hits_override is not None else set(env.hits)
    misses = misses_override if misses_override is not None else set(env.misses)

    for y in range(size):
        for x in range(size):
            cell = (x, y)
            if cell in hits:
                grid[2][y][x] = 1.0  # agent_hit
            elif cell in misses:
                grid[1][y][x] = 1.0  # agent_miss
            else:
                grid[0][y][x] = 1.0  # agent_unknown

    if last_player_shot:
        lx, ly = last_player_shot
        if 0 <= lx < size and 0 <= ly < size:
            grid[3][ly][lx] = 1.0
    if last_agent_shot:
        ax, ay = last_agent_shot
        if 0 <= ax < size and 0 <= ay < size:
            grid[4][ay][ax] = 1.0

    channel_offset = len(DEFAULT_CHANNEL_NAMES)

    if include_self:
        for y in range(size):
            for x in range(size):
                grid[channel_offset][y][x] = 1.0  # self_unknown
        channel_offset += 2

    if include_hit_cluster:
        cluster_idx = channel_offset
        for hx, hy in hits:
            for nx, ny in _neighbors((hx, hy)):
                if (
                    0 <= nx < size
                    and 0 <= ny < size
                    and (nx, ny) not in hits
                    and (nx, ny) not in misses
                ):
                    grid[cluster_idx][ny][nx] = 1.0

    action_mask = []
    for y in range(size):
        for x in range(size):
            action_mask.append(1 if (x, y) not in hits and (x, y) not in misses else 0)

    scalars = [move_fraction, remaining_fraction]

    return EncodedState(
        grid=grid, action_mask=action_mask, scalars=scalars, channel_names=channel_names
    )


def encode_state_np(
    hits,
    misses,
    moves_taken: int,
    max_moves: int,
    last_player_shot: Optional[Coordinate] = None,
    last_agent_shot: Optional[Coordinate] = None,
    include_hit_cluster: bool = True,
):
    """Vectorized encoder for numpy boolean hits/misses arrays."""
    import numpy as np

    size = hits.shape[0]
    unknown = ~(hits | misses)
    channel_list = [
        unknown.astype(np.float32),  # agent_unknown
        misses.astype(np.float32),  # agent_miss
        hits.astype(np.float32),  # agent_hit
        np.zeros_like(hits, dtype=np.float32),  # last_player_shot
        np.zeros_like(hits, dtype=np.float32),  # last_agent_shot
    ]
    if last_player_shot:
        lx, ly = last_player_shot
        if 0 <= lx < size and 0 <= ly < size:
            channel_list[3][ly, lx] = 1.0
    if last_agent_shot:
        ax, ay = last_agent_shot
        if 0 <= ax < size and 0 <= ay < size:
            channel_list[4][ay, ax] = 1.0

    if include_hit_cluster:
        cluster = np.zeros_like(hits, dtype=np.float32)
        ys, xs = np.nonzero(hits)
        for x, y in zip(xs, ys, strict=False):
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < size and 0 <= ny < size and unknown[ny, nx]:
                    cluster[ny, nx] = 1.0
        channel_list.append(cluster)

    grid = np.stack(channel_list, axis=0)
    mask = unknown.astype(np.int32).reshape(-1).tolist()
    return grid, mask

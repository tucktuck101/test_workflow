import random
from typing import List, Sequence, Tuple

Coordinate = Tuple[int, int]


def _extract_masks(board, board_size: int):
    """
    Accepts either:
      - a tuple/list of (hits, misses) where each is a set of coords or numpy bool array
      - an object with .hits and .misses attributes (set or numpy bool array)
    Returns (unknown_mask, hits_set).
    """
    if isinstance(board, (list, tuple)) and len(board) >= 2:
        hits, misses = board[0], board[1]
    else:
        hits = getattr(board, "hits", None)
        misses = getattr(board, "misses", None)
    if hits is None or misses is None:
        raise ValueError("board must provide hits and misses")

    hits_set: set[Coordinate] = set()
    miss_set: set[Coordinate] = set()
    if hasattr(hits, "shape"):  # numpy array
        import numpy as np

        ys, xs = np.nonzero(hits)
        hits_set.update(zip(xs.tolist(), ys.tolist()))
    else:
        hits_set.update(hits)

    if hasattr(misses, "shape"):
        import numpy as np

        ys, xs = np.nonzero(misses)
        miss_set.update(zip(xs.tolist(), ys.tolist()))
    else:
        miss_set.update(misses)

    unknown = []
    for y in range(board_size):
        for x in range(board_size):
            coord = (x, y)
            if coord in hits_set or coord in miss_set:
                unknown.append(False)
            else:
                unknown.append(True)
    return unknown, hits_set


def _unknown_indices(board, board_size: int) -> List[int]:
    unknown_mask, _ = _extract_masks(board, board_size)
    return [i for i, flag in enumerate(unknown_mask) if flag]


def random_bot_action(board, board_size: int) -> int:
    """Uniform over unknown cells; returns flat index y*board_size + x."""
    unknown = _unknown_indices(board, board_size)
    if not unknown:
        return 0
    return random.choice(unknown)


class HuntTargetBot:
    def __init__(self, board_size: int):
        self.board_size = board_size
        self.mode = "hunt"
        self.hit_cells: List[Coordinate] = []
        self.candidate_dirs: List[Coordinate] = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        self.parity = 0
        self.known_hits: set[Coordinate] = set()

    def _reset_target(self):
        self.mode = "hunt"
        self.hit_cells = []
        self.candidate_dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def _hunt_action(self, board) -> int:
        unknown_mask, hits_set = _extract_masks(board, self.board_size)
        candidates = []
        for idx, is_unknown in enumerate(unknown_mask):
            if not is_unknown:
                continue
            x = idx % self.board_size
            y = idx // self.board_size
            if (x + y) % 2 == self.parity:
                candidates.append(idx)
        if not candidates:
            candidates = [i for i, flag in enumerate(unknown_mask) if flag]
        if not candidates:
            return 0
        choice = random.choice(candidates)
        return choice

    def _line_unknown(self, hits: List[Coordinate], board) -> int | None:
        # Determine orientation and pick closest unknown at either end
        unknown_mask, _ = _extract_masks(board, self.board_size)
        xs = [h[0] for h in hits]
        ys = [h[1] for h in hits]
        if len(set(xs)) == 1:
            x = xs[0]
            min_y, max_y = min(ys), max(ys)
            # extend up then down
            for y in range(min_y - 1, -1, -1):
                idx = y * self.board_size + x
                if unknown_mask[idx]:
                    return idx
                else:
                    break
            for y in range(max_y + 1, self.board_size):
                idx = y * self.board_size + x
                if unknown_mask[idx]:
                    return idx
                else:
                    break
        elif len(set(ys)) == 1:
            y = ys[0]
            min_x, max_x = min(xs), max(xs)
            for x in range(min_x - 1, -1, -1):
                idx = y * self.board_size + x
                if unknown_mask[idx]:
                    return idx
                else:
                    break
            for x in range(max_x + 1, self.board_size):
                idx = y * self.board_size + x
                if unknown_mask[idx]:
                    return idx
                else:
                    break
        return None

    def _target_action(self, board) -> int:
        unknown_mask, hits_set = _extract_masks(board, self.board_size)
        # Refresh hit_cells from observed hits
        if not hits_set:
            self._reset_target()
            return self._hunt_action(board)
        if not self.hit_cells:
            self.hit_cells = sorted(hits_set)
        else:
            # extend known hits with any new ones
            for h in hits_set:
                if h not in self.hit_cells:
                    self.hit_cells.append(h)
        self.hit_cells = sorted(set(self.hit_cells))

        if len(self.hit_cells) >= 2:
            idx = self._line_unknown(self.hit_cells, board)
            if idx is not None and unknown_mask[idx]:
                return idx
            # assume sunk, reset
            self._reset_target()
            return self._hunt_action(board)

        # single hit: try candidate directions sequentially
        hx, hy = self.hit_cells[0]
        while self.candidate_dirs:
            dx, dy = self.candidate_dirs[0]
            nx, ny = hx + dx, hy + dy
            if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                idx = ny * self.board_size + nx
                if unknown_mask[idx]:
                    return idx
            # discard direction and try next
            self.candidate_dirs.pop(0)
        # no directions left; reset to hunt
        self._reset_target()
        return self._hunt_action(board)

    def select_action(self, board) -> int:
        unknown_mask, hits_set = _extract_masks(board, self.board_size)
        # Detect new hits to switch into target mode
        new_hits = hits_set - self.known_hits
        self.known_hits = hits_set
        if new_hits:
            if self.mode != "target":
                self.mode = "target"
                self.hit_cells = sorted(hits_set)
        if self.mode == "target" and not hits_set:
            self._reset_target()
        if self.mode == "hunt":
            return self._hunt_action(board)
        return self._target_action(board)


class ProbabilityBot:
    def __init__(self, board_size: int, remaining_ships: Sequence[int] | None = None):
        self.board_size = board_size
        self.remaining_ships = list(remaining_ships) if remaining_ships is not None else [5, 4, 3, 3, 2]
        self.target_bot = HuntTargetBot(board_size)

    def _score_board(self, hits_set: set[Coordinate], miss_set: set[Coordinate]) -> List[int]:
        size = self.board_size
        scores = [0] * (size * size)
        for ship_len in self.remaining_ships:
            # horizontal
            for y in range(size):
                for x in range(size - ship_len + 1):
                    cells = [(x + i, y) for i in range(ship_len)]
                    if any(c in miss_set for c in cells):
                        continue
                    if any(h not in cells for h in hits_set):
                        continue
                    for cx, cy in cells:
                        scores[cy * size + cx] += 1
            # vertical
            for x in range(size):
                for y in range(size - ship_len + 1):
                    cells = [(x, y + i) for i in range(ship_len)]
                    if any(c in miss_set for c in cells):
                        continue
                    if any(h not in cells for h in hits_set):
                        continue
                    for cx, cy in cells:
                        scores[cy * size + cx] += 1
        return scores

    def select_action(self, board) -> int:
        unknown_mask, hits_set = _extract_masks(board, self.board_size)
        miss_set = set()
        if isinstance(board, (list, tuple)) and len(board) >= 2:
            misses = board[1]
        else:
            misses = getattr(board, "misses", None)
        if misses is not None:
            if hasattr(misses, "shape"):
                import numpy as np

                ys, xs = np.nonzero(misses)
                miss_set.update(zip(xs.tolist(), ys.tolist()))
            else:
                miss_set.update(misses)

        # Target mode fallback to HuntTargetBot logic when hits exist
        if hits_set:
            return self.target_bot.select_action(board)

        scores = self._score_board(hits_set, miss_set)
        best_score = -1
        best_indices: List[int] = []
        for idx, is_unknown in enumerate(unknown_mask):
            if not is_unknown:
                continue
            s = scores[idx]
            if s > best_score:
                best_score = s
                best_indices = [idx]
            elif s == best_score:
                best_indices.append(idx)
        if not best_indices:
            return random_bot_action(board, self.board_size)
        return random.choice(best_indices)

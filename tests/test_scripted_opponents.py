import random

from bots.scripted_opponents import HuntTargetBot, ProbabilityBot, random_bot_action

BOARD_SIZE = 10


def _full_misses_except(targets):
    misses = set()
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if (x, y) in targets:
                continue
            misses.add((x, y))
    return misses


def test_random_bot_action_legal_unknown_only():
    random.seed(0)
    hits = {(0, 0), (1, 1)}
    misses = {(2, 2), (3, 3)}
    for _ in range(20):
        idx = random_bot_action((hits, misses), BOARD_SIZE)
        x = idx % BOARD_SIZE
        y = idx // BOARD_SIZE
        assert (x, y) not in hits
        assert (x, y) not in misses


def test_hunt_target_prefers_parity_when_only_one_cell_available():
    bot = HuntTargetBot(BOARD_SIZE)
    keep_unknown = {(2, 2)}  # parity 0 cell
    misses = _full_misses_except(keep_unknown)
    idx = bot.select_action((set(), misses))
    assert idx == keep_unknown.pop()[1] * BOARD_SIZE + 2


def test_hunt_target_single_hit_targets_only_open_neighbor():
    bot = HuntTargetBot(BOARD_SIZE)
    hit = (5, 5)
    # Block all neighbors except up
    misses = {(5, 6), (6, 5), (4, 5)}
    idx = bot.select_action(({hit}, misses))
    assert idx == (4 * BOARD_SIZE + 5)  # (5,4)


def test_probability_bot_heatmap_picks_unique_best_cell():
    # Only a single vertical strip of 5 unknown cells at x=0, y=0..4; all others are misses
    misses = set()
    hits = set()
    unknown_strip = {(0, y) for y in range(5)}
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if (x, y) in unknown_strip:
                continue
            misses.add((x, y))
    bot = ProbabilityBot(BOARD_SIZE)
    idx = bot.select_action((hits, misses))
    # Middle of the strip (x=0, y=2) should have highest overlap
    assert idx == 2 * BOARD_SIZE + 0

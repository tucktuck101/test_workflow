import pytest

from app import engine


def test_create_session_deterministic():
    session1 = engine.create_session(board_size=10, deterministic_seed=42)
    session2 = engine.create_session(board_size=10, deterministic_seed=42)

    coords1 = sorted(c for ship in session1.agent_ships for c in ship.coordinates)
    coords2 = sorted(c for ship in session2.agent_ships for c in ship.coordinates)
    assert coords1 == coords2


def test_apply_player_move_hit_and_sunk():
    session = engine.create_session(board_size=5, deterministic_seed=1)
    target_ship = session.agent_ships[0]
    coord = target_ship.coordinates[0]

    result = engine.apply_player_move(session, coord)
    assert result["outcome"] in {engine.MoveOutcome.HIT.value, engine.MoveOutcome.SUNK.value}
    assert session.agent_board_hits[coord] in {engine.MoveOutcome.HIT, engine.MoveOutcome.SUNK}

    # Sink the ship
    for c in target_ship.coordinates[1:]:
        engine.apply_player_move(session, c)
    assert target_ship.is_sunk


def test_apply_agent_move_win_transition():
    session = engine.create_session(board_size=5, deterministic_seed=2)
    target_ship = session.player_ships[0]
    for c in target_ship.coordinates:
        engine.apply_agent_move(session, c)
    assert session.status in {engine.GameStatus.AGENT_WON, engine.GameStatus.IN_PROGRESS}


def test_duplicate_move_rejected():
    session = engine.create_session(board_size=5, deterministic_seed=3)
    coord = session.agent_ships[0].coordinates[0]
    engine.apply_player_move(session, coord)
    with pytest.raises(engine.InvalidMove):
        engine.apply_player_move(session, coord)


def test_out_of_bounds_rejected():
    session = engine.create_session(board_size=5, deterministic_seed=4)
    with pytest.raises(engine.InvalidMove):
        engine.apply_player_move(session, (-1, 0))


def test_finished_game_rejects_moves():
    session = engine.create_session(board_size=5, deterministic_seed=5)
    session.status = engine.GameStatus.QUIT
    with pytest.raises(engine.GameFinished):
        engine.apply_player_move(session, (0, 0))


def test_session_store_capacity():
    store = engine.InMemorySessionStore(max_active_games=1)
    s1 = store.create(board_size=5, deterministic_seed=1)
    assert store.get(s1.game_id)
    with pytest.raises(engine.InvalidMove):
        store.create(board_size=5)
    store.end(s1.game_id)
    assert store.active_count == 0

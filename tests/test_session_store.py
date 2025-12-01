from app.engine import InMemorySessionStore


def test_session_store_ttl_expires(monkeypatch):
    store = InMemorySessionStore(max_active_games=2, ttl_seconds=0)
    session = store.create(board_size=5)
    assert store.get(session.game_id) is None


def test_session_store_end_removes(monkeypatch):
    store = InMemorySessionStore(max_active_games=2, ttl_seconds=10)
    session = store.create(board_size=5)
    assert store.get(session.game_id)
    store.end(session.game_id)
    assert store.get(session.game_id) is None
    assert store.active_count == 0

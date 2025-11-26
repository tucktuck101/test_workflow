from app.agent import AgentAdapter
from app.engine import GameSession, create_session


def test_agent_deterministic_returns_same_move():
    session = create_session(board_size=5, deterministic_seed=123)
    agent_det = AgentAdapter(deterministic=True)
    first = agent_det.next_move(session)
    # Reset a fresh session with same seed to compare
    session2 = create_session(board_size=5, deterministic_seed=123)
    second = agent_det.next_move(session2)
    assert first == second


def test_agent_non_deterministic_varies():
    session = create_session(board_size=5, deterministic_seed=None)
    agent_non = AgentAdapter(deterministic=False)
    move1 = agent_non.next_move(session)
    # mark that move as taken to force different outcome next call
    session.player_board_hits[move1] = session.player_board_hits.get(move1, None) or None
    move2 = agent_non.next_move(session)
    assert move1 != move2

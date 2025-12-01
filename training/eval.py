import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from .env import BattleshipEnv, Coordinate, DEFAULT_SHIPS


def _load_policy(path: Path) -> Dict[Coordinate, float]:
    data = json.loads(path.read_text())
    policy: Dict[Coordinate, float] = {}
    for key, value in data.items():
        x, y = key.split(",")
        policy[(int(x), int(y))] = float(value)
    return policy


def _greedy_action(env: BattleshipEnv, policy: Dict[Coordinate, float]) -> Coordinate:
    actions = env.available_actions()
    if not actions:
        return (0, 0)
    return max(actions, key=lambda a: policy.get(a, 0.0))


def evaluate(
    policy_path: Path,
    episodes: int = 10,
    board_size: int = 5,
    seed: int = 0,
    ships: Optional[List[Tuple[str, int]]] = None,
    allow_adjacent: bool = True,
) -> Tuple[float, float]:
    policy = _load_policy(policy_path)
    env = BattleshipEnv(board_size=board_size, seed=seed, ships=ships or list(DEFAULT_SHIPS), allow_adjacent=allow_adjacent)
    total_reward = 0.0
    total_moves = 0
    for _ in range(episodes):
        env.reset()
        done = False
        while not done:
            action = _greedy_action(env, policy)
            reward, done = env.step(action)
            total_reward += reward
            total_moves += 1
    return total_reward / episodes, total_moves / episodes


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate trained policy")
    parser.add_argument("--artifact", required=True, help="Path to policy artifact (JSON)")
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--board-size", type=int, default=5)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--disallow-adjacent", dest="allow_adjacent", action="store_false", help="Disallow ships touching (diag/edge)")
    parser.set_defaults(allow_adjacent=True)
    args = parser.parse_args()

    mean_reward, mean_moves = evaluate(
        Path(args.artifact),
        args.episodes,
        args.board_size,
        args.seed,
        ships=None,
        allow_adjacent=args.allow_adjacent,
    )
    print(json.dumps({"mean_reward": mean_reward, "mean_moves": mean_moves}, indent=2))


if __name__ == "__main__":
    main()

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .env import BattleshipEnv, Coordinate


@dataclass
class QLearner:
    env: BattleshipEnv
    epsilon: float = 0.2
    lr: float = 0.1
    gamma: float = 0.95

    def __post_init__(self) -> None:
        self.q: Dict[Tuple[int, int], float] = {}
        self.rng = random.Random(self.env.seed)

    def _key(self, action: Coordinate) -> Tuple[int, int]:
        return action

    def select_action(self) -> Coordinate:
        actions = self.env.available_actions()
        if not actions:
            return (0, 0)
        if self.rng.random() < self.epsilon:
            return self.rng.choice(actions)
        # exploit: pick max Q
        best = max(actions, key=lambda a: self.q.get(self._key(a), 0.0))
        return best

    def update(self, action: Coordinate, reward: float, done: bool) -> None:
        key = self._key(action)
        old_q = self.q.get(key, 0.0)
        next_max = 0.0
        if not done:
            next_actions = self.env.available_actions()
            if next_actions:
                next_max = max(self.q.get(self._key(a), 0.0) for a in next_actions)
        new_q = old_q + self.lr * (reward + self.gamma * next_max - old_q)
        self.q[key] = new_q

    def train_episode(self) -> float:
        self.env.reset()
        total_reward = 0.0
        done = False
        while not done:
            action = self.select_action()
            reward, done = self.env.step(action)
            self.update(action, reward, done)
            total_reward += reward
        return total_reward

    def train(self, episodes: int) -> List[float]:
        rewards = []
        for _ in range(episodes):
            rewards.append(self.train_episode())
        return rewards

    def export_policy(self) -> Dict[str, float]:
        # export as flat map key="x,y" -> q-value
        return {f"{x},{y}": q for (x, y), q in self.q.items()}

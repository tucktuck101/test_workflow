import csv
import json
import math
import sys
import os
from collections import deque, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Deque, List, Optional, Tuple

import numpy as np

from training.config import TrainConfig
from training.config_loader import apply_overrides, dataclass_field_names, load_yaml_config, validate_values, validate_yaml_sections
from training.env import DEFAULT_SHIPS
from training.state_encoder import encode_state, encode_state_np
from training.vectorized_env import VectorEnv, BatchedEnv


def rollout_worker_fn(args):
    policy_params, env_params, opponent_params, eps, episodes, seed, batch_envs = args

    def clone(val):
        return val.copy() if hasattr(val, "copy") else val

    rng = np.random.default_rng(seed)
    batch_env = BatchedEnv(batch_size=batch_envs, params=env_params, seed=seed)
    model_type = policy_params.get("model_type", "mlp")
    board_size = env_params["board_size"]
    use_dueling = policy_params.get("use_dueling", False)
    if model_type == "cnn":
        conv1 = clone(policy_params["conv1"])
        conv2 = clone(policy_params["conv2"])
        conv_channels = (conv1.shape[0], conv2.shape[0])
        input_channels = conv1.shape[1]
        hidden = policy_params["wa"].shape[0] if use_dueling else policy_params["w3"].shape[0]
        q = NumpyDQN(
            board_size * board_size * input_channels,
            board_size * board_size,
            hidden=hidden,
            use_dueling=use_dueling,
            model=model_type,
            input_channels=input_channels,
            board_size=board_size,
            conv_channels=conv_channels,
        )
        q.conv1, q.conv1_b = conv1, clone(policy_params["conv1_b"])
        q.conv2, q.conv2_b = conv2, clone(policy_params["conv2_b"])
        q.fc, q.fc_b = clone(policy_params["fc"]), clone(policy_params["fc_b"])
        if use_dueling:
            q.wv, q.bv, q.wa, q.ba = [clone(policy_params[k]) for k in ("wv", "bv", "wa", "ba")]
        else:
            q.w3, q.b3 = [clone(policy_params[k]) for k in ("w3", "b3")]
    else:
        input_dim = policy_params["w1"].shape[0]
        hidden = policy_params["w1"].shape[1]
        q = NumpyDQN(input_dim, board_size * board_size, hidden=hidden, use_dueling=use_dueling, model=model_type)
        q.w1, q.b1, q.w2, q.b2 = [clone(policy_params[k]) for k in ("w1", "b1", "w2", "b2")]
        if use_dueling:
            q.wv, q.bv, q.wa, q.ba = [clone(policy_params[k]) for k in ("wv", "bv", "wa", "ba")]
        else:
            q.w3, q.b3 = [clone(policy_params[k]) for k in ("w3", "b3")]
    bot = None
    if opponent_params and opponent_params.get("bot_type"):
        from bots.scripted_opponents import HuntTargetBot, ProbabilityBot, random_bot_action

        bot_type = opponent_params["bot_type"]
        if bot_type == "random":
            bot = ("random", random_bot_action)
        elif bot_type == "hunt_target":
            bot = ("hunt_target", HuntTargetBot(board_size))
        elif bot_type == "probability":
            ships = opponent_params.get("ships") or DEFAULT_SHIPS
            lengths = [s for _, s in ships]
            bot = ("probability", ProbabilityBot(board_size, remaining_ships=lengths))
    transitions = []
    summaries = []
    ep_counter = 0
    for _ in range(episodes):
        batch_env.reset()
        dones = [False] * batch_env.batch_size
        last_actions: List[Optional[Coordinate]] = [None] * batch_env.batch_size
        reward_components = [defaultdict(float) for _ in range(batch_env.batch_size)]
        while not all(dones):
            actions: List[Coordinate] = []
            grids: List[Optional[np.ndarray]] = []
            masks: List[Optional[List[int]]] = []
            states = batch_env.get_states()
            for idx, (hits, misses, moves_taken, max_moves) in enumerate(states):
                if dones[idx]:
                    actions.append((0, 0))
                    grids.append(None)
                    masks.append(None)
                    continue
                grid, mask = encode_state_np(hits, misses, moves_taken, max_moves, last_actions[idx], None, include_hit_cluster=True)
                if bot and bot[0] in {"random", "hunt_target", "probability"}:
                    _, bot_impl = bot
                    if bot[0] == "random":
                        idx_action = bot_impl((hits, misses), board_size)
                    else:
                        idx_action = bot_impl.select_action((hits, misses))
                    action = (idx_action % board_size, idx_action // board_size)
                else:
                    action = select_action(q, grid, mask, eps)
                actions.append(action)
                grids.append(grid)
                masks.append(mask)
            prev_states = states
            rewards, step_dones = batch_env.step(actions)
            new_states = batch_env.get_states()
            for i in range(batch_env.batch_size):
                if dones[i]:
                    continue
                next_hits, next_misses, next_moves, next_max = new_states[i]
                next_grid, next_mask = encode_state_np(next_hits, next_misses, next_moves, next_max, actions[i], None, include_hit_cluster=True)
                transitions.append((grids[i], actions[i], rewards[i], next_grid, step_dones[i], masks[i]))
                last_actions[i] = actions[i]
                # reward breakdown
                prev_hits, prev_misses, prev_moves, _ = prev_states[i]
                breakdown = reward_breakdown(batch_env.envs[i], actions[i], rewards[i], step_dones[i], prev_hits, prev_misses, prev_moves)
                for k, v in breakdown.items():
                    reward_components[i][k] += v
                dones[i] = step_dones[i]
                if step_dones[i]:
                    summary = {
                        "episode": ep_counter,
                        "outcome": 1 if next_hits.sum() == 0 else 0,
                        "p1_moves": next_moves,
                        "p2_moves": None,
                    }
                    summary.update(reward_components[i])
                    summaries.append(summary)
                    ep_counter += 1
    return transitions, summaries
from training.trainer import sha256_bytes

Coordinate = Tuple[int, int]


@dataclass
class DQNConfig:
    gamma: float = 0.99
    buffer_size: int = 20000
    batch_size: int = 64
    target_update: int = 200
    epsilon_start: float = 1.0
    epsilon_end: float = 0.05
    epsilon_min: float = 0.05
    epsilon_decay: int = 10000
    lr: float = 3e-4
    warmup_steps: int = 1000
    clip_norm: Optional[float] = 1.0
    use_huber: bool = True
    huber_delta: float = 1.0
    double_dqn: bool = True
    use_dueling: bool = True
    model: str = "mlp"
    hidden: int = 256
    conv_channels: Tuple[int, int] = (16, 32)

    @classmethod
    def from_env(cls) -> "DQNConfig":
        conv_raw = os.getenv("DQN_CONV_CHANNELS", "16,32")

        def _parse_channels(val: str) -> Tuple[int, int]:
            try:
                parts = [int(p) for p in val.split(",") if p.strip()]
                if len(parts) == 2:
                    return parts[0], parts[1]
            except ValueError:
                pass
            return cls.conv_channels

        return cls(
            gamma=float(os.getenv("DQN_GAMMA", "0.99")),
            buffer_size=int(os.getenv("DQN_BUFFER", "20000")),
            batch_size=int(os.getenv("DQN_BATCH", "64")),
            target_update=int(os.getenv("DQN_TARGET_UPDATE", "200")),
            epsilon_start=float(os.getenv("DQN_EPS_START", "1.0")),
            epsilon_end=float(os.getenv("DQN_EPS_END", os.getenv("DQN_EPS_MIN", "0.05"))),
            epsilon_min=float(os.getenv("DQN_EPS_MIN", os.getenv("DQN_EPS_END", "0.05"))),
            epsilon_decay=int(os.getenv("DQN_EPS_DECAY_STEPS", os.getenv("DQN_EPS_DECAY", "10000"))),
            lr=float(os.getenv("DQN_LR", "0.0003")),
            warmup_steps=int(os.getenv("DQN_WARMUP_STEPS", "1000")),
            clip_norm=float(os.getenv("DQN_CLIP_NORM", "1.0")) if os.getenv("DQN_CLIP_NORM", "1.0") else None,
            use_huber=os.getenv("DQN_USE_HUBER", "1").lower() in {"1", "true", "yes", "on"},
            huber_delta=float(os.getenv("DQN_HUBER_DELTA", "1.0")),
            double_dqn=os.getenv("DQN_DOUBLE", "1").lower() in {"1", "true", "yes", "on"},
            use_dueling=os.getenv("DQN_DUELING", "1").lower() in {"1", "true", "yes", "on"},
            model=os.getenv("DQN_MODEL", "mlp"),
            hidden=int(os.getenv("DQN_HIDDEN", "256")),
            conv_channels=_parse_channels(conv_raw),
        )


@dataclass
class SelfPlayConfig:
    chunk_episodes: int = 5000
    max_rounds: int = 20
    snapshot_interval: int = 500
    baseline_games: int = 0
    baseline_threshold: float = 0.0
    baseline_workers: int = 1
    eval_games: int = 200
    eval_threshold: float = 0.7
    eval_workers: int = 1
    loss_penalty: float = 5.0
    metrics_path: Optional[Path] = None
    rollout_workers: int = 1
    batch_size: int = 1
    move_gate: Optional[float] = None
    progress_log: bool = True
    progress_path: Optional[Path] = None

    @classmethod
    def from_env(cls) -> "SelfPlayConfig":
        import os

        return cls(
            chunk_episodes=int(os.getenv("DQN_SELFPLAY_CHUNK", "5000")),
            max_rounds=int(os.getenv("DQN_SELFPLAY_MAX_ROUNDS", "20")),
            snapshot_interval=int(os.getenv("DQN_SELFPLAY_SNAPSHOT", "500")),
            baseline_games=int(os.getenv("DQN_BASELINE_GAMES", "0")),
            baseline_threshold=float(os.getenv("DQN_BASELINE_THRESHOLD", "0.0")),
            baseline_workers=max(1, int(os.getenv("DQN_BASELINE_WORKERS", "1"))),
            eval_games=int(os.getenv("DQN_SELFPLAY_EVAL_GAMES", "200")),
            eval_threshold=float(os.getenv("DQN_SELFPLAY_THRESHOLD", "0.7")),
            eval_workers=max(1, int(os.getenv("DQN_SELFPLAY_EVAL_WORKERS", "1"))),
            loss_penalty=float(os.getenv("DQN_SELFPLAY_LOSS_PENALTY", "5.0")),
            metrics_path=Path(os.getenv("DQN_METRICS_PATH")).expanduser().resolve() if os.getenv("DQN_METRICS_PATH") else None,
            rollout_workers=max(1, int(os.getenv("DQN_ROLLOUT_WORKERS", "1"))),
            batch_size=max(1, int(os.getenv("DQN_BATCH_ENVS", "1"))),
            move_gate=float(os.getenv("DQN_MOVE_GATE", "nan")) if os.getenv("DQN_MOVE_GATE") else None,
            progress_log=os.getenv("DQN_PROGRESS_LOG", "1").lower() in {"1", "true", "yes", "on"},
            progress_path=Path(os.getenv("DQN_PROGRESS_PATH")).expanduser().resolve() if os.getenv("DQN_PROGRESS_PATH") else None,
        )


class ReplayBuffer:
    def __init__(self, capacity: int):
        self.buffer: Deque = deque(maxlen=capacity)

    def push(self, *transition):
        self.buffer.append(tuple(transition))

    def extend(self, transitions: List[tuple]):
        self.buffer.extend(transitions)

    def sample(self, batch_size: int):
        import random

        batch = random.sample(self.buffer, batch_size)
        return map(list, zip(*batch))

    def __len__(self):
        return len(self.buffer)


class NumpyDQN:
    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        hidden: int = 256,
        use_dueling: bool = False,
        model: str = "mlp",
        input_channels: Optional[int] = None,
        board_size: Optional[int] = None,
        conv_channels: Tuple[int, int] = (16, 32),
    ):
        rng = np.random.default_rng()
        self.use_dueling = use_dueling
        self.model_type = model
        self.board_size = board_size
        self.input_channels = input_channels
        self.conv_channels = conv_channels
        self.output_dim = output_dim
        self.hidden = hidden
        if model == "cnn":
            if input_channels is None or board_size is None:
                raise ValueError("CNN model requires input_channels and board_size")
            c1, c2 = conv_channels
            self.conv1 = rng.normal(0, 0.1, (c1, input_channels, 3, 3))
            self.conv1_b = np.zeros((1, c1, 1, 1))
            self.conv2 = rng.normal(0, 0.1, (c2, c1, 3, 3))
            self.conv2_b = np.zeros((1, c2, 1, 1))
            flat_dim = c2 * board_size * board_size
            self.fc = rng.normal(0, 0.1, (flat_dim, hidden))
            self.fc_b = np.zeros((1, hidden))
        else:
            self.w1 = rng.normal(0, 0.1, (input_dim, hidden))
            self.b1 = np.zeros((1, hidden))
            self.w2 = rng.normal(0, 0.1, (hidden, hidden))
            self.b2 = np.zeros((1, hidden))
        if use_dueling:
            self.wv = rng.normal(0, 0.1, (hidden, 1))
            self.bv = np.zeros((1, 1))
            self.wa = rng.normal(0, 0.1, (hidden, output_dim))
            self.ba = np.zeros((1, output_dim))
        else:
            self.w3 = rng.normal(0, 0.1, (hidden, output_dim))
            self.b3 = np.zeros((1, output_dim))

    def copy(self) -> "NumpyDQN":
        twin = NumpyDQN(
            input_dim=1,
            output_dim=self.output_dim,
            hidden=self.hidden,
            use_dueling=self.use_dueling,
            model=self.model_type,
            input_channels=self.input_channels,
            board_size=self.board_size,
            conv_channels=self.conv_channels,
        )
        if self.model_type == "cnn":
            twin.conv1, twin.conv1_b = self.conv1.copy(), self.conv1_b.copy()
            twin.conv2, twin.conv2_b = self.conv2.copy(), self.conv2_b.copy()
            twin.fc, twin.fc_b = self.fc.copy(), self.fc_b.copy()
        else:
            twin.w1, twin.b1 = self.w1.copy(), self.b1.copy()
            twin.w2, twin.b2 = self.w2.copy(), self.b2.copy()
        if self.use_dueling:
            twin.wv, twin.bv = self.wv.copy(), self.bv.copy()
            twin.wa, twin.ba = self.wa.copy(), self.ba.copy()
        else:
            twin.w3, twin.b3 = self.w3.copy(), self.b3.copy()
        return twin

    def _conv2d(self, x: np.ndarray, weight: np.ndarray, b: np.ndarray, padding: int = 1):
        batch, _, h, w_in = x.shape
        k = weight.shape[2]
        x_pad = np.pad(x, ((0, 0), (0, 0), (padding, padding), (padding, padding)))
        out = np.zeros((batch, weight.shape[0], h, w_in))
        for i in range(h):
            for j in range(w_in):
                region = x_pad[:, :, i : i + k, j : j + k]
                out[:, :, i, j] = np.tensordot(region, weight, axes=([1, 2, 3], [1, 2, 3]))
        out = out + b
        cache = {"x_pad": x_pad}
        return out, cache

    def _conv2d_backward(self, grad_out: np.ndarray, x_pad: np.ndarray, weight: np.ndarray, padding: int = 1):
        batch, out_channels, h, w_in = grad_out.shape
        _, in_channels, k, _ = weight.shape
        grad_x_pad = np.zeros_like(x_pad)
        grad_w = np.zeros_like(weight)
        grad_b = np.sum(grad_out, axis=(0, 2, 3), keepdims=True)
        for i in range(h):
            for j in range(w_in):
                region = x_pad[:, :, i : i + k, j : j + k]
                grad_w += np.tensordot(grad_out[:, :, i, j], region, axes=([0], [0]))
                for b_idx in range(batch):
                    grad_x_pad[b_idx, :, i : i + k, j : j + k] += np.sum(
                        grad_out[b_idx, :, i, j][:, None, None, None] * weight, axis=0
                    )
        if padding > 0:
            grad_x = grad_x_pad[:, :, padding:-padding, padding:-padding]
        else:
            grad_x = grad_x_pad
        return grad_x, grad_w, grad_b

    def forward(self, x: np.ndarray, board_size: Optional[int] = None) -> Tuple[np.ndarray, dict]:
        if self.model_type == "cnn":
            if x.ndim == 2:
                if board_size is None:
                    board_size = self.board_size
                channels = self.input_channels
                x = x.reshape(x.shape[0], channels, board_size, board_size)
            conv1_out, cache_c1 = self._conv2d(x, self.conv1, self.conv1_b, padding=1)
            h1 = np.maximum(0, conv1_out)
            conv2_out, cache_c2 = self._conv2d(h1, self.conv2, self.conv2_b, padding=1)
            h2 = np.maximum(0, conv2_out)
            flat = h2.reshape(h2.shape[0], -1)
            z3 = flat @ self.fc + self.fc_b
            h3 = np.maximum(0, z3)
            if self.use_dueling:
                v = h3 @ self.wv + self.bv
                a = h3 @ self.wa + self.ba
                out = v + (a - np.mean(a, axis=1, keepdims=True))
            else:
                out = h3 @ self.w3 + self.b3
            cache = {
                "x": x,
                "conv1": cache_c1,
                "conv1_out": conv1_out,
                "h1": h1,
                "conv2": cache_c2,
                "conv2_out": conv2_out,
                "h2": h2,
                "flat": flat,
                "z3": z3,
                "h3": h3,
            }
            return out, cache
        if x.ndim > 2:
            x = x.reshape(x.shape[0], -1)
        z1 = x @ self.w1 + self.b1
        h1 = np.maximum(0, z1)
        z2 = h1 @ self.w2 + self.b2
        h2 = np.maximum(0, z2)
        if self.use_dueling:
            v = h2 @ self.wv + self.bv
            a = h2 @ self.wa + self.ba
            out = v + (a - np.mean(a, axis=1, keepdims=True))
        else:
            out = h2 @ self.w3 + self.b3
        cache = {"x": x, "z1": z1, "h1": h1, "z2": z2, "h2": h2}
        return out, cache

    def parameters(self) -> dict:
        if self.model_type == "cnn":
            params = {
                "conv1": self.conv1,
                "conv1_b": self.conv1_b,
                "conv2": self.conv2,
                "conv2_b": self.conv2_b,
                "fc": self.fc,
                "fc_b": self.fc_b,
                "model_type": self.model_type,
                "conv_channels": np.array(self.conv_channels),
            }
        else:
            params = {"w1": self.w1, "b1": self.b1, "w2": self.w2, "b2": self.b2, "model_type": self.model_type}
        if self.use_dueling:
            params.update({"wv": self.wv, "bv": self.bv, "wa": self.wa, "ba": self.ba, "use_dueling": True})
        else:
            params.update({"w3": self.w3, "b3": self.b3, "use_dueling": False})
        return params

    def save(self, path: Path) -> None:
        params = self.parameters()
        np.savez(path, **params)


def relu_backward(grad: np.ndarray, z: np.ndarray) -> np.ndarray:
    g = grad.copy()
    g[z <= 0] = 0
    return g


def encode_env_state(env, last_action: Optional[Coordinate]) -> Tuple[np.ndarray, List[int]]:
    # Vectorized env has numpy hits/misses; fallback to default encoder otherwise
    if hasattr(env, "hits") and isinstance(env.hits, np.ndarray):
        last_agent = None  # not tracked here
        grid, mask = encode_state_np(env.hits, env.misses, env.moves_taken, env.max_moves, last_action, last_agent, include_hit_cluster=True)
        return grid, mask
    encoded = encode_state(env, last_player_shot=last_action, include_hit_cluster=True)
    grid = np.array(encoded.grid, dtype=np.float32)
    return grid, encoded.action_mask


def select_action(q_net: NumpyDQN, grid: np.ndarray, mask: List[int], epsilon: float) -> Coordinate:
    import random

    size = int(math.sqrt(len(mask)))
    if random.random() < epsilon:
        legal = [i for i, m in enumerate(mask) if m == 1]
        choice = random.choice(legal)
        return (choice % size, choice // size)
    if q_net.model_type == "cnn":
        q_vals, _ = q_net.forward(grid[np.newaxis, ...], board_size=size)
    else:
        q_vals, _ = q_net.forward(grid.reshape(1, -1))
    q_vals = q_vals.reshape(-1)
    mask_arr = np.array(mask, dtype=bool)
    q_vals = np.where(mask_arr, q_vals, -1e9)
    idx = int(np.argmax(q_vals))
    return (idx % size, idx // size)


def reward_breakdown(env, action: Coordinate, reward: float, done: bool, prev_hits, prev_misses, prev_moves: int) -> dict:
    """Reconstruct reward components based on env state before the step."""
    def _to_set(mask):
        if hasattr(mask, "shape"):
            ys, xs = mask.nonzero()
            return set(zip(xs.tolist(), ys.tolist()))
        return set(mask)

    step_reward = env._step_penalty(prev_moves + 1) if hasattr(env, "_step_penalty") else 0.0
    hit_reward = 0.0
    miss_reward = 0.0
    sink_reward = 0.0
    win_reward = 0.0
    loss_reward = 0.0
    duplicate_penalty = getattr(env, "duplicate_penalty", 0.0)

    prev_hits_set = _to_set(prev_hits)
    prev_misses_set = _to_set(prev_misses)
    is_dup = action in prev_hits_set or action in prev_misses_set
    is_hit = False
    if hasattr(env, "agent_board"):
        if hasattr(env.agent_board, "shape"):
            x, y = action
            is_hit = bool(env.agent_board[y, x])
        else:
            is_hit = action in env.agent_board

    if is_dup:
        step_reward -= duplicate_penalty
    elif is_hit:
        hit_reward = getattr(env, "reward_hit", 0.0)
        # sink detection
        if hasattr(env, "cell_to_ship"):
            ship_idx = env.cell_to_ship.get(action, None)
            if ship_idx is not None and hasattr(env, "ship_remaining") and env.ship_remaining[ship_idx] == 0:
                sink_reward = getattr(env, "reward_sink_mult", 0.0) * len(env.ship_cells[ship_idx])
        elif hasattr(env, "ship_id"):
            x, y = action
            ship_idx = int(env.ship_id[y, x]) - 1
            if ship_idx >= 0 and ship_idx < len(env.ship_remaining):
                if env.ship_remaining[ship_idx] == 0:
                    sink_reward = getattr(env, "reward_sink_mult", 0.0) * env.ship_sizes[ship_idx]
        if hasattr(env, "remaining") and env.remaining == 0:
            decay = 0.0
            if getattr(env, "reward_win_decay_k", 0) > 0:
                decay = max(0.0, 1 - max(0, prev_moves + 1 - env.reward_perfect_move) / env.reward_win_decay_k)
            win_reward = getattr(env, "reward_win_max", 0.0) * decay
    else:
        miss_reward = getattr(env, "reward_miss", 0.0)

    if done and hasattr(env, "remaining") and env.remaining > 0:
        loss_reward = getattr(env, "reward_loss", 0.0)

    total = step_reward + hit_reward + miss_reward + sink_reward + win_reward + loss_reward
    return {
        "step_reward": step_reward,
        "hit_reward": hit_reward,
        "miss_reward": miss_reward,
        "sink_reward": sink_reward,
        "win_reward": win_reward,
        "loss_reward": loss_reward,
        "total_reward": total,
    }


def _clip_gradients(grad_list: List[np.ndarray], clip_norm: Optional[float]) -> None:
    if clip_norm is None or clip_norm <= 0:
        return
    total_norm = 0.0
    for g in grad_list:
        total_norm += float(np.sum(g * g))
    total_norm = math.sqrt(total_norm)
    if total_norm > clip_norm and total_norm > 0:
        scale = clip_norm / (total_norm + 1e-8)
        for g in grad_list:
            g *= scale


def train_step(
    batch,
    q_net: NumpyDQN,
    target_net: NumpyDQN,
    gamma: float,
    lr: float,
    board_size: int,
    clip_norm: Optional[float],
    use_huber: bool,
    huber_delta: float,
    double_dqn: bool,
):
    states, actions, rewards, next_states, dones, masks = batch
    state_arr = np.array(states, dtype=np.float32)
    next_state_arr = np.array(next_states, dtype=np.float32)
    actions = np.array(actions, dtype=np.int64)
    rewards = np.array(rewards, dtype=np.float32)
    dones = np.array(dones, dtype=bool)
    masks_arr = np.array(masks, dtype=bool)

    if q_net.model_type == "mlp":
        forward_states = state_arr.reshape(len(states), -1)
        forward_next_states = next_state_arr.reshape(len(next_states), -1)
    else:
        forward_states = state_arr
        forward_next_states = next_state_arr

    q_vals, cache = q_net.forward(forward_states, board_size=board_size if q_net.model_type == "cnn" else None)
    idx = actions[:, 1] * board_size + actions[:, 0]
    chosen_q = q_vals[range(len(states)), idx]

    next_q_online, _ = q_net.forward(forward_next_states, board_size=board_size if q_net.model_type == "cnn" else None)
    next_q_target, _ = target_net.forward(forward_next_states, board_size=board_size if q_net.model_type == "cnn" else None)
    next_q_online = next_q_online.reshape(len(states), -1)
    next_q_target = next_q_target.reshape(len(states), -1)
    next_q_online = np.where(masks_arr, next_q_online, -1e9)
    next_q_target = np.where(masks_arr, next_q_target, -1e9)
    if double_dqn:
        next_actions = np.argmax(next_q_online, axis=1)
        next_max = next_q_target[range(len(states)), next_actions]
    else:
        next_max = np.max(next_q_target, axis=1)
    targets = rewards + gamma * next_max * (~dones)

    diff = chosen_q - targets
    if use_huber:
        grad_output = np.where(np.abs(diff) <= huber_delta, diff, huber_delta * np.sign(diff))
    else:
        grad_output = diff
    grad_output = grad_output / len(states)

    grad_out_full = np.zeros_like(q_vals)
    grad_out_full[range(len(states)), idx] = grad_output

    grad_tensors: List[np.ndarray] = []

    if q_net.model_type == "cnn":
        if q_net.use_dueling:
            grad_a = grad_out_full
            mean_grad_a = np.mean(grad_a, axis=1, keepdims=True)
            grad_a = grad_a - mean_grad_a
            grad_h3_a = grad_a @ q_net.wa.T
            grad_wa = cache["h3"].T @ grad_a
            grad_ba = np.sum(grad_a, axis=0, keepdims=True)

            grad_v_scalar = np.sum(grad_out_full, axis=1, keepdims=True)
            grad_h3_v = grad_v_scalar @ q_net.wv.T
            grad_wv = cache["h3"].T @ grad_v_scalar
            grad_bv = np.sum(grad_v_scalar, axis=0, keepdims=True)

            grad_h3 = grad_h3_a + grad_h3_v
            grad_tensors.extend([grad_wa, grad_ba, grad_wv, grad_bv])
        else:
            grad_h3 = grad_out_full @ q_net.w3.T
            grad_w3 = cache["h3"].T @ grad_out_full
            grad_b3 = np.sum(grad_out_full, axis=0, keepdims=True)
            grad_tensors.extend([grad_w3, grad_b3])

        grad_h3 = relu_backward(grad_h3, cache["z3"])
        grad_flat = grad_h3 @ q_net.fc.T
        grad_fc = cache["flat"].T @ grad_h3
        grad_fc_b = np.sum(grad_h3, axis=0, keepdims=True)
        grad_tensors.extend([grad_fc, grad_fc_b])

        grad_h2 = grad_flat.reshape(cache["h2"].shape)
        grad_h2 = relu_backward(grad_h2, cache["conv2_out"])
        grad_h1, grad_conv2, grad_conv2_b = q_net._conv2d_backward(grad_h2, cache["conv2"]["x_pad"], q_net.conv2, padding=1)
        grad_tensors.extend([grad_conv2, grad_conv2_b])

        grad_h1 = relu_backward(grad_h1, cache["conv1_out"])
        grad_input, grad_conv1, grad_conv1_b = q_net._conv2d_backward(grad_h1, cache["conv1"]["x_pad"], q_net.conv1, padding=1)
        grad_tensors.extend([grad_conv1, grad_conv1_b])

        _clip_gradients(grad_tensors, clip_norm)

        if q_net.use_dueling:
            q_net.wa -= lr * grad_wa
            q_net.ba -= lr * grad_ba
            q_net.wv -= lr * grad_wv
            q_net.bv -= lr * grad_bv
        else:
            q_net.w3 -= lr * grad_w3
            q_net.b3 -= lr * grad_b3
        q_net.fc -= lr * grad_fc
        q_net.fc_b -= lr * grad_fc_b
        q_net.conv2 -= lr * grad_conv2
        q_net.conv2_b -= lr * grad_conv2_b
        q_net.conv1 -= lr * grad_conv1
        q_net.conv1_b -= lr * grad_conv1_b
    else:
        if q_net.use_dueling:
            # Advantage path
            grad_a = grad_out_full
            mean_grad_a = np.mean(grad_a, axis=1, keepdims=True)
            grad_a = grad_a - mean_grad_a
            grad_h2_a = grad_a @ q_net.wa.T
            grad_wa = cache["h2"].T @ grad_a
            grad_ba = np.sum(grad_a, axis=0, keepdims=True)

            # Value path (scalar)
            grad_v_scalar = np.sum(grad_out_full, axis=1, keepdims=True)
            grad_h2_v = grad_v_scalar @ q_net.wv.T
            grad_wv = cache["h2"].T @ grad_v_scalar
            grad_bv = np.sum(grad_v_scalar, axis=0, keepdims=True)

            grad_h2 = grad_h2_a + grad_h2_v
            grad_tensors.extend([grad_wa, grad_ba, grad_wv, grad_bv])
        else:
            grad_h2 = grad_out_full @ q_net.w3.T
            grad_w3 = cache["h2"].T @ grad_out_full
            grad_b3 = np.sum(grad_out_full, axis=0, keepdims=True)
            grad_tensors.extend([grad_w3, grad_b3])

        grad_h2 = relu_backward(grad_h2, cache["z2"])
        grad_h1 = grad_h2 @ q_net.w2.T
        grad_w2 = cache["h1"].T @ grad_h2
        grad_b2 = np.sum(grad_h2, axis=0, keepdims=True)

        grad_h1 = relu_backward(grad_h1, cache["z1"])
        grad_w1 = cache["x"].T @ grad_h1
        grad_b1 = np.sum(grad_h1, axis=0, keepdims=True)
        grad_tensors.extend([grad_w2, grad_b2, grad_w1, grad_b1])

        _clip_gradients(grad_tensors, clip_norm)

        if q_net.use_dueling:
            q_net.wa -= lr * grad_wa
            q_net.ba -= lr * grad_ba
            q_net.wv -= lr * grad_wv
            q_net.bv -= lr * grad_bv
        else:
            q_net.w3 -= lr * grad_w3
            q_net.b3 -= lr * grad_b3
        q_net.w2 -= lr * grad_w2
        q_net.b2 -= lr * grad_b2
        q_net.w1 -= lr * grad_w1
        q_net.b1 -= lr * grad_b1


def play_game(policy: NumpyDQN, opponent: Optional[NumpyDQN], env_params: dict, seed: int) -> tuple[bool, int, int]:
    rng = np.random.default_rng(seed)
    env_me = VectorEnv(seed=seed, **env_params)
    env_opp = VectorEnv(seed=seed + 1, **env_params)
    board_size = env_params["board_size"]
    last_me = last_opp = None
    while True:
        grid, mask = encode_env_state(env_opp, last_me)
        action_me = select_action(policy, grid, mask, epsilon=0.0)
        env_opp.step(action_me)
        last_me = action_me
        if env_opp.remaining == 0:
            return True, env_me.moves_taken, env_opp.moves_taken
        # opponent
        if opponent is None:
            legal = [i for i, m in enumerate(mask) if m == 1]
            if not legal:
                return False, env_me.moves_taken, env_opp.moves_taken
            choice = rng.choice(legal)
            action_opp = (choice % board_size, choice // board_size)
        elif isinstance(opponent, tuple) and opponent[0] in {"random", "hunt_target", "probability"}:
            bot_kind, bot_impl = opponent
            if bot_kind == "random":
                idx = bot_impl((env_me.hits, env_me.misses), board_size)
            else:
                idx = bot_impl.select_action((env_me.hits, env_me.misses))
            action_opp = (idx % board_size, idx // board_size)
        else:
            grid_o, mask_o = encode_env_state(env_me, last_opp)
            action_opp = select_action(opponent, grid_o, mask_o, epsilon=0.0)
        env_me.step(action_opp)
        last_opp = action_opp
        if env_me.remaining == 0:
            return False, env_me.moves_taken, env_opp.moves_taken
        if env_me.moves_taken >= env_me.max_moves or env_opp.moves_taken >= env_opp.max_moves:
            return False, env_me.moves_taken, env_opp.moves_taken


def _play_game_args(args):
    policy_params, opponent_params, env_params, seed = args

    def clone(val):
        return val.copy() if hasattr(val, "copy") else val

    model_type = policy_params.get("model_type", "mlp")
    use_dueling = policy_params.get("use_dueling", False)
    if model_type == "cnn":
        conv1 = clone(policy_params["conv1"])
        conv2 = clone(policy_params["conv2"])
        conv_channels = (conv1.shape[0], conv2.shape[0])
        input_channels = conv1.shape[1]
        hidden = policy_params["wa"].shape[0] if use_dueling else policy_params["w3"].shape[0]
        policy = NumpyDQN(
            board_size * board_size * input_channels,
            board_size * board_size,
            hidden=hidden,
            use_dueling=use_dueling,
            model=model_type,
            input_channels=input_channels,
            board_size=board_size,
            conv_channels=conv_channels,
        )
        policy.conv1, policy.conv1_b = conv1, clone(policy_params["conv1_b"])
        policy.conv2, policy.conv2_b = conv2, clone(policy_params["conv2_b"])
        policy.fc, policy.fc_b = clone(policy_params["fc"]), clone(policy_params["fc_b"])
        if use_dueling:
            policy.wv, policy.bv, policy.wa, policy.ba = [clone(policy_params[k]) for k in ("wv", "bv", "wa", "ba")]
        else:
            policy.w3, policy.b3 = [clone(policy_params[k]) for k in ("w3", "b3")]
    else:
        input_dim = policy_params["w1"].shape[0]
        hidden = policy_params["w1"].shape[1]
        policy = NumpyDQN(input_dim, board_size * board_size, hidden=hidden, use_dueling=use_dueling, model=model_type)
        policy.w1, policy.b1, policy.w2, policy.b2 = [clone(policy_params[k]) for k in ("w1", "b1", "w2", "b2")]
        if policy.use_dueling:
            policy.wv, policy.bv, policy.wa, policy.ba = [clone(policy_params[k]) for k in ("wv", "bv", "wa", "ba")]
        else:
            policy.w3, policy.b3 = [clone(policy_params[k]) for k in ("w3", "b3")]
    opponent = None
    if opponent_params:
        bot_type = opponent_params.get("bot_type")
        if bot_type:
            from bots.scripted_opponents import HuntTargetBot, ProbabilityBot, random_bot_action

            if bot_type == "random":
                opponent = ("random", random_bot_action)
            elif bot_type == "hunt_target":
                opponent = ("hunt_target", HuntTargetBot(board_size))
            elif bot_type == "probability":
                ships = opponent_params.get("ships") or DEFAULT_SHIPS
                lengths = [s for _, s in ships]
                opponent = ("probability", ProbabilityBot(board_size, remaining_ships=lengths))
        else:
            opp_model = opponent_params.get("model_type", "mlp")
            opp_dueling = opponent_params.get("use_dueling", False)
            if opp_model == "cnn":
                conv1 = clone(opponent_params["conv1"])
                conv2 = clone(opponent_params["conv2"])
                conv_channels = (conv1.shape[0], conv2.shape[0])
                input_channels = conv1.shape[1]
                hidden = opponent_params["wa"].shape[0] if opp_dueling else opponent_params["w3"].shape[0]
                opponent = NumpyDQN(
                    board_size * board_size * input_channels,
                    board_size * board_size,
                    hidden=hidden,
                    use_dueling=opp_dueling,
                    model=opp_model,
                    input_channels=input_channels,
                    board_size=board_size,
                    conv_channels=conv_channels,
                )
                opponent.conv1, opponent.conv1_b = conv1, clone(opponent_params["conv1_b"])
                opponent.conv2, opponent.conv2_b = conv2, clone(opponent_params["conv2_b"])
                opponent.fc, opponent.fc_b = clone(opponent_params["fc"]), clone(opponent_params["fc_b"])
                if opp_dueling:
                    opponent.wv, opponent.bv, opponent.wa, opponent.ba = [clone(opponent_params[k]) for k in ("wv", "bv", "wa", "ba")]
                else:
                    opponent.w3, opponent.b3 = [clone(opponent_params[k]) for k in ("w3", "b3")]
            else:
                input_dim = opponent_params["w1"].shape[0]
                hidden = opponent_params["w1"].shape[1]
                opponent = NumpyDQN(input_dim, board_size * board_size, hidden=hidden, use_dueling=opp_dueling, model=opp_model)
                opponent.w1, opponent.b1, opponent.w2, opponent.b2 = [clone(opponent_params[k]) for k in ("w1", "b1", "w2", "b2")]
                if opponent.use_dueling:
                    opponent.wv, opponent.bv, opponent.wa, opponent.ba = [clone(opponent_params[k]) for k in ("wv", "bv", "wa", "ba")]
                else:
                    opponent.w3, opponent.b3 = [clone(opponent_params[k]) for k in ("w3", "b3")]
    return play_game(policy, opponent, env_params, seed)


def evaluate_policy(
    policy: NumpyDQN,
    opponent: Optional[NumpyDQN] | Optional[str],
    games: int,
    env_params: dict,
    seed: int,
    workers: int = 1,
    opponent_label: str = "",
) -> tuple[float, list]:
    if games == 0:
        return 0.0, []
    seeds = [seed + i * 17 for i in range(games)]
    summaries = []
    ships = env_params.get("ships") or DEFAULT_SHIPS

    def _make_bot(bot_type: str):
        from bots.scripted_opponents import HuntTargetBot, ProbabilityBot, random_bot_action

        if bot_type == "random":
            return ("random", random_bot_action)
        if bot_type == "hunt_target":
            return ("hunt_target", HuntTargetBot(env_params["board_size"]))
        if bot_type == "probability":
            lengths = [s for _, s in ships]
            return ("probability", ProbabilityBot(env_params["board_size"], remaining_ships=lengths))
        raise ValueError(f"unknown bot_type {bot_type}")

    opponent_is_bot = isinstance(opponent, str)
    if workers <= 1:
        wins = 0
        for s in seeds:
            opp_inst = _make_bot(opponent) if opponent_is_bot else opponent
            win, p1_moves, p2_moves = play_game(policy, opp_inst, env_params, s)
            wins += 1 if win else 0
            summaries.append({"opponent": opponent_label, "outcome": 1 if win else 0, "p1_moves": p1_moves, "p2_moves": p2_moves})
        return wins / games, summaries
    policy_params = {**policy.parameters(), "model_type": policy.model_type}
    opponent_params = None
    if isinstance(opponent, str):
        opponent_params = {"bot_type": opponent, "ships": ships}
    elif opponent:
        opponent_params = {**opponent.parameters(), "model_type": opponent.model_type}
    args = [(policy_params, opponent_params, env_params, s) for s in seeds]
    import multiprocessing as mp

    with mp.Pool(processes=workers) as pool:
        results = pool.map(_play_game_args, args)
    wins = 0
    for win, p1_moves, p2_moves in results:
        wins += 1 if win else 0
        summaries.append({"opponent": opponent_label, "outcome": 1 if win else 0, "p1_moves": p1_moves, "p2_moves": p2_moves})
    return wins / games, summaries


def run_dqn_selfplay(cfg: TrainConfig, dqn_cfg: DQNConfig, sp_cfg: SelfPlayConfig, opponent_type: Optional[str] = None) -> dict:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    debug = os.getenv("DQN_DEBUG", "0").lower() in {"1", "true", "yes", "on"}
    env_params = {
        "board_size": cfg.board_size,
        "ships": cfg.ships or DEFAULT_SHIPS,
        "allow_adjacent": cfg.allow_adjacent,
        "reward_step_base": cfg.reward_step_base,
        "reward_step_decay": cfg.reward_step_decay,
        "reward_step_cap": cfg.reward_step_cap,
        "reward_hit": cfg.reward_hit,
        "reward_miss": cfg.reward_miss,
        "reward_sink_mult": cfg.reward_sink_mult,
        "reward_win_max": cfg.reward_win_max,
        "reward_win_decay_k": cfg.reward_win_decay_k,
        "reward_loss": cfg.reward_loss,
        "reward_perfect_move": cfg.reward_perfect_move,
    }
    env = VectorEnv(seed=cfg.seed, **env_params)
    channels = 6
    input_dim = channels * cfg.board_size * cfg.board_size
    output_dim = cfg.board_size * cfg.board_size
    q_net = NumpyDQN(
        input_dim,
        output_dim,
        hidden=dqn_cfg.hidden,
        use_dueling=dqn_cfg.use_dueling,
        model=dqn_cfg.model,
        input_channels=channels,
        board_size=cfg.board_size,
        conv_channels=dqn_cfg.conv_channels,
    )
    target_net = q_net.copy()
    buffer = ReplayBuffer(dqn_cfg.buffer_size)
    metrics_path = sp_cfg.metrics_path or (cfg.output_dir / f"dqn_selfplay_metrics-{run_id}.csv")
    progress_path = sp_cfg.progress_path or (cfg.output_dir / f"dqn_progress-{run_id}.jsonl")
    log_counter = 1

    def dlog(msg: str) -> None:
        if debug:
            print(f"[dqn-debug] {msg}", file=sys.stderr, flush=True)

    def log_progress(data: dict) -> None:
        if not sp_cfg.progress_log:
            return
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"timestamp": datetime.now(timezone.utc).isoformat(), **data}
        with progress_path.open("a") as pf:
            pf.write(json.dumps(payload) + "\n")

    metric_fields = [
        "timestamp",
        "phase",
        "round",
        "episode",
        "opponent",
        "epsilon",
        "outcome",
        "p1_moves",
        "p2_moves",
        "total_reward",
        "step_reward",
        "hit_reward",
        "miss_reward",
        "sink_reward",
        "win_reward",
        "loss_reward",
    ]

    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with metrics_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=metric_fields)
        writer.writeheader()
        writer.writerow({"timestamp": datetime.now(timezone.utc).isoformat(), "phase": "run_start", "round": 0, "episode": 0, "opponent": None, "epsilon": dqn_cfg.epsilon_start, "outcome": None, "p1_moves": None, "p2_moves": None})
    log_progress({"event": "run_start", "run_id": run_id, "epsilon": dqn_cfg.epsilon_start})

    def log_metrics(row: dict) -> None:
        if not metrics_path:
            return
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with metrics_path.open("a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=metric_fields)
            if "timestamp" not in row:
                row["timestamp"] = datetime.now(timezone.utc).isoformat()
            # assign a monotonically increasing episode id for every log row to ensure uniqueness across phases
            nonlocal log_counter
            row["episode"] = log_counter
            log_counter += 1
            writer.writerow(row)

    epsilon = dqn_cfg.epsilon_start
    eps_min = dqn_cfg.epsilon_min
    eps_decay = (dqn_cfg.epsilon_start - eps_min) / max(1, dqn_cfg.epsilon_decay)

    def decay_eps(eps: float) -> float:
        if eps > eps_min:
            return max(eps_min, eps - eps_decay)
        return eps

    def train_round(opponent: Optional[NumpyDQN], start_episode: int) -> int:
        nonlocal epsilon, q_net, target_net
        global_ep = start_episode
        if sp_cfg.rollout_workers <= 1:
            # single-process rollout
            for ep in range(start_episode, start_episode + sp_cfg.chunk_episodes):
                env.reset()
                done = False
                last_action: Optional[Coordinate] = None
                comp = defaultdict(float)
                while not done:
                    grid, mask = encode_env_state(env, last_action)
                    action = select_action(q_net, grid, mask, epsilon)
                    prev_hits, prev_misses, prev_remaining, prev_moves = env.hits.copy(), env.misses.copy(), env.remaining, env.moves_taken
                    reward, done = env.step(action)
                    breakdown = reward_breakdown(env, action, reward, done, prev_hits, prev_misses, prev_moves)
                    for k, v in breakdown.items():
                        comp[k] += v
                    next_grid, next_mask = encode_env_state(env, action)
                    buffer.push(grid, action, reward, next_grid, done, next_mask)
                    if len(buffer) >= dqn_cfg.batch_size:
                        batch = buffer.sample(dqn_cfg.batch_size)
                        train_step(
                            batch,
                            q_net,
                            target_net,
                            dqn_cfg.gamma,
                            dqn_cfg.lr,
                            cfg.board_size,
                            dqn_cfg.clip_norm,
                            dqn_cfg.use_huber,
                            dqn_cfg.huber_delta,
                            dqn_cfg.double_dqn,
                        )
                    epsilon = decay_eps(epsilon)
                    last_action = action
                if ep % dqn_cfg.target_update == 0:
                    target_net = q_net.copy()
                outcome = 1 if env.remaining == 0 else 0
                log_row = {
                    "phase": "train",
                    "round": round_idx,
                    "episode": global_ep,
                    "opponent": "self",
                    "epsilon": epsilon,
                    "outcome": outcome,
                    "p1_moves": env.moves_taken,
                    "p2_moves": None,
                }
                log_row.update(comp)
                log_metrics(log_row)
                global_ep += 1
                if ep % cfg.log_interval == 0:
                    print(f"[dqn-selfplay] ep={ep} eps={epsilon:.3f}", file=sys.stderr, flush=True)
        else:
            # multi-process rollout
            import multiprocessing as mp

            policy_params = {**q_net.parameters(), "model_type": q_net.model_type}
            per_worker = math.ceil(sp_cfg.chunk_episodes / sp_cfg.rollout_workers)
            seeds = [cfg.seed + round_idx * 1000 + i for i in range(sp_cfg.rollout_workers)]
            params = [(policy_params, env_params, None, epsilon, per_worker, s, sp_cfg.batch_size) for s in seeds]
            dlog(f"rollout mp: workers={sp_cfg.rollout_workers} per_worker={per_worker} batch_envs={sp_cfg.batch_size}")
            with mp.Pool(processes=sp_cfg.rollout_workers) as pool:
                results = pool.map(rollout_worker_fn, params)
            for transitions, summaries in results:
                buffer.extend(transitions)
                for s in summaries:
                    row = {
                        "phase": "train",
                        "round": round_idx,
                        "episode": global_ep,
                        "opponent": "self",
                        "epsilon": epsilon,
                        "outcome": s["outcome"],
                        "p1_moves": s.get("p1_moves"),
                        "p2_moves": s.get("p2_moves"),
                    }
                    for key in ("total_reward", "step_reward", "hit_reward", "miss_reward", "sink_reward", "win_reward", "loss_reward"):
                        if key in s:
                            row[key] = s[key]
                    log_metrics(row)
                    global_ep += 1
            # train on accumulated buffer
            total_steps = sp_cfg.chunk_episodes * sp_cfg.batch_size
            steps = 0
            while steps < total_steps:
                if len(buffer) >= dqn_cfg.batch_size:
                    batch = buffer.sample(dqn_cfg.batch_size)
                    train_step(
                        batch,
                        q_net,
                        target_net,
                        dqn_cfg.gamma,
                        dqn_cfg.lr,
                        cfg.board_size,
                        dqn_cfg.clip_norm,
                        dqn_cfg.use_huber,
                        dqn_cfg.huber_delta,
                        dqn_cfg.double_dqn,
                    )
                if steps > dqn_cfg.warmup_steps:
                    epsilon = decay_eps(epsilon)
                steps += 1
            target_net = q_net.copy()
            current_ep = global_ep - 1
            print(f"[dqn-selfplay] round={round_idx} episodes={current_ep} eps={epsilon:.3f}", file=sys.stderr, flush=True)
        return global_ep

    dlog(
        f"start run_id={run_id} rollout_workers={sp_cfg.rollout_workers} batch_envs={sp_cfg.batch_size} "
        f"baseline_games={sp_cfg.baseline_games} eval_games={sp_cfg.eval_games} metrics={metrics_path}"
    )

    current_episode = 1
    for round_idx in range(1, sp_cfg.max_rounds + 1):
        current_episode = train_round(target_net, current_episode)
        log_progress({"event": "train_round_complete", "round": round_idx, "epsilon": epsilon, "buffer": len(buffer)})
        # baseline eval vs random
        if sp_cfg.baseline_games > 0:
            baseline_wr, baseline_summaries = evaluate_policy(
                q_net,
                opponent_type if opponent_type else None,
                sp_cfg.baseline_games,
                env_params,
                cfg.seed + round_idx,
                workers=sp_cfg.baseline_workers,
                opponent_label="baseline",
            )
            print(f"[dqn-selfplay] round {round_idx} baseline win_rate={baseline_wr:.3f}", file=sys.stderr, flush=True)
            dlog(f"baseline eval done round={round_idx} wr={baseline_wr:.3f}")
            for s in baseline_summaries:
                log_metrics({"phase": "baseline_eval", "round": round_idx, "episode": current_episode, "opponent": s["opponent"], "epsilon": epsilon, "outcome": s["outcome"], "p1_moves": s.get("p1_moves"), "p2_moves": s.get("p2_moves")})
            if baseline_wr < sp_cfg.baseline_threshold:
                if round_idx == sp_cfg.max_rounds:
                    raise RuntimeError(f"baseline win_rate {baseline_wr:.3f} below threshold {sp_cfg.baseline_threshold}")
                continue
            log_progress({"event": "baseline_eval", "round": round_idx, "win_rate": baseline_wr, "games": sp_cfg.baseline_games})

        snapshot = q_net.copy()
        eval_opponent = opponent_type if opponent_type else snapshot
        wr, eval_summaries = evaluate_policy(
            q_net,
            eval_opponent,
            sp_cfg.eval_games,
            env_params,
            cfg.seed + round_idx * 3,
            workers=sp_cfg.eval_workers,
            opponent_label="selfplay_eval",
        )
        print(f"[dqn-selfplay] round {round_idx} self win_rate={wr:.3f}", file=sys.stderr, flush=True)
        dlog(f"selfplay eval done round={round_idx} wr={wr:.3f}")
        for s in eval_summaries:
            log_metrics({"phase": "selfplay_eval", "round": round_idx, "episode": current_episode, "opponent": s["opponent"], "epsilon": epsilon, "outcome": s["outcome"], "p1_moves": s.get("p1_moves"), "p2_moves": s.get("p2_moves")})
        move_values = [s.get("p1_moves") for s in eval_summaries if s.get("p1_moves") is not None]
        avg_moves = sum(move_values) / len(move_values) if move_values else None
        log_progress({"event": "selfplay_eval", "round": round_idx, "win_rate": wr, "games": sp_cfg.eval_games, "avg_moves": avg_moves})
        if wr >= sp_cfg.eval_threshold and (sp_cfg.move_gate is None or (avg_moves is not None and avg_moves <= sp_cfg.move_gate)):
            artifact_name = cfg.artifact_name if cfg.artifact_name.endswith(".npz") else f"{cfg.artifact_name}.npz"
            artifact_path = cfg.output_dir / artifact_name
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            q_net.save(artifact_path)
            digest = sha256_bytes(artifact_path.read_bytes())
            manifest = {
                "version": cfg.version,
                "hash": digest,
                "artifact": artifact_path.name,
                "board_size": cfg.board_size,
                "ships": cfg.ships or DEFAULT_SHIPS,
                "allow_adjacent": cfg.allow_adjacent,
                "model_type": "dqn_numpy",
                "input_channels": channels,
                "architecture": dqn_cfg.model,
                "dueling": dqn_cfg.use_dueling,
                "double_dqn": dqn_cfg.double_dqn,
                "use_huber": dqn_cfg.use_huber,
                "conv_channels": list(dqn_cfg.conv_channels),
                "reward_step_base": cfg.reward_step_base,
                "reward_step_decay": cfg.reward_step_decay,
                "reward_step_cap": cfg.reward_step_cap,
                "reward_hit": cfg.reward_hit,
                "reward_miss": cfg.reward_miss,
                "reward_sink_mult": cfg.reward_sink_mult,
                "reward_win_max": cfg.reward_win_max,
                "reward_win_decay_k": cfg.reward_win_decay_k,
                "reward_perfect_move": cfg.reward_perfect_move,
                "reward_loss": cfg.reward_loss,
                "win_rate": wr,
                "eval_games": sp_cfg.eval_games,
                "avg_moves": avg_moves,
                "move_gate": sp_cfg.move_gate,
                "threshold": sp_cfg.eval_threshold,
                "baseline_games": sp_cfg.baseline_games,
                "baseline_threshold": sp_cfg.baseline_threshold,
                "run_id": run_id,
            }
            manifest_path = cfg.output_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, indent=2))
            summary = {
                "run_id": run_id,
                "artifact": str(artifact_path),
                "manifest": str(manifest_path),
                "hash": digest,
                "win_rate": wr,
                "avg_moves": avg_moves,
                "baseline_games": sp_cfg.baseline_games,
                "baseline_threshold": sp_cfg.baseline_threshold,
            }
            summary_path = cfg.output_dir / f"dqn_selfplay_run-{run_id}.json"
            summary_path.write_text(json.dumps(summary, indent=2))
            return summary
        else:
            if wr >= sp_cfg.eval_threshold and sp_cfg.move_gate is not None and (avg_moves is None or avg_moves > sp_cfg.move_gate):
                print(f"[dqn-selfplay] round {round_idx} win_rate ok but avg_moves={avg_moves} above gate {sp_cfg.move_gate}", file=sys.stderr, flush=True)
    raise RuntimeError(f"self-play win_rate did not reach threshold {sp_cfg.eval_threshold}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run DQN self-play training")
    parser.add_argument("--opponent", choices=["random", "hunt_target", "probability"], default=None, help="Scripted opponent for evaluation (baseline/random by default)")
    parser.add_argument("--config", type=str, default=None, help="Path to YAML config for training")
    args = parser.parse_args()

    yaml_data = {}
    if args.config:
        yaml_data = load_yaml_config(args.config)
        required = ["train", "dqn", "selfplay"]
        allowed = {
            "train": dataclass_field_names(TrainConfig),
            "dqn": dataclass_field_names(DQNConfig),
            "selfplay": dataclass_field_names(SelfPlayConfig),
        }
        validate_yaml_sections(yaml_data, required, allowed)

    cfg = TrainConfig.from_env()
    dqn_cfg = DQNConfig.from_env()
    sp_cfg = SelfPlayConfig.from_env()

    train_data = yaml_data.get("train", {}) if yaml_data else {}
    dqn_data = yaml_data.get("dqn", {}) if yaml_data else {}
    sp_data = yaml_data.get("selfplay", {}) if yaml_data else {}
    yaml_opponent = yaml_data.get("opponent") if yaml_data else None

    if train_data:
        apply_overrides(cfg, train_data)
    if dqn_data:
        apply_overrides(dqn_cfg, dqn_data)
        if isinstance(dqn_cfg.conv_channels, list):
            dqn_cfg.conv_channels = tuple(int(v) for v in dqn_cfg.conv_channels)
    if sp_data:
        apply_overrides(sp_cfg, sp_data)
    validate_values(cfg, dqn_cfg, sp_cfg)

    opponent = args.opponent or yaml_opponent

    result = run_dqn_selfplay(cfg, dqn_cfg, sp_cfg, opponent_type=opponent)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

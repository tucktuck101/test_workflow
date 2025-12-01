import json
import math
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, List, Optional, Tuple

import numpy as np

from training.config import TrainConfig
from training.env import BattleshipEnv, DEFAULT_SHIPS
from training.state_encoder import encode_state
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
    max_episodes: int = 20000
    clip_norm: Optional[float] = 1.0
    use_huber: bool = True
    huber_delta: float = 1.0
    double_dqn: bool = True
    use_dueling: bool = False
    model: str = "mlp"  # mlp|cnn
    hidden: int = 256
    conv_channels: Tuple[int, int] = (16, 32)

    @classmethod
    def from_env(cls) -> "DQNConfig":
        import os

        def _parse_channels(val: str) -> Tuple[int, int]:
            try:
                parts = [int(p) for p in val.split(",") if p.strip()]
                if len(parts) == 2:
                    return parts[0], parts[1]
            except ValueError:
                pass
            return cls.conv_channels

        eps_end = float(os.getenv("DQN_EPS_END", os.getenv("DQN_EPS_MIN", "0.05")))
        eps_decay = int(os.getenv("DQN_EPS_DECAY_STEPS", os.getenv("DQN_EPS_DECAY", "10000")))
        clip_norm_val = os.getenv("DQN_CLIP_NORM", "1.0")
        clip_norm = float(clip_norm_val) if clip_norm_val else None
        return cls(
            gamma=float(os.getenv("DQN_GAMMA", "0.99")),
            buffer_size=int(os.getenv("DQN_BUFFER", "20000")),
            batch_size=int(os.getenv("DQN_BATCH", "64")),
            target_update=int(os.getenv("DQN_TARGET_UPDATE", "200")),
            epsilon_start=float(os.getenv("DQN_EPS_START", "1.0")),
            epsilon_end=eps_end,
            epsilon_min=eps_end,
            epsilon_decay=eps_decay,
            lr=float(os.getenv("DQN_LR", "0.0003")),
            max_episodes=int(os.getenv("DQN_MAX_EPISODES", "20000")),
            clip_norm=clip_norm,
            use_huber=os.getenv("DQN_USE_HUBER", "1").lower() in {"1", "true", "yes", "on"},
            huber_delta=float(os.getenv("DQN_HUBER_DELTA", "1.0")),
            double_dqn=os.getenv("DQN_DOUBLE", "1").lower() in {"1", "true", "yes", "on"},
            use_dueling=os.getenv("DQN_DUELING", "0").lower() in {"1", "true", "yes", "on"},
            model=os.getenv("DQN_MODEL", "mlp"),
            hidden=int(os.getenv("DQN_HIDDEN", "256")),
            conv_channels=_parse_channels(os.getenv("DQN_CONV_CHANNELS", "16,32")),
        )


class ReplayBuffer:
    def __init__(self, capacity: int):
        self.buffer: Deque = deque(maxlen=capacity)

    def push(self, *transition):
        self.buffer.append(tuple(transition))

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
        model: str = "mlp",
        input_channels: Optional[int] = None,
        board_size: Optional[int] = None,
        conv_channels: Tuple[int, int] = (16, 32),
        use_dueling: bool = False,
    ):
        rng = np.random.default_rng()
        self.model_type = model
        self.use_dueling = use_dueling
        self.board_size = board_size
        self.input_channels = input_channels
        self.output_dim = output_dim
        self.conv_channels = conv_channels
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
            hidden=self.wv.shape[0] if self.use_dueling else self.w3.shape[0],
            model=self.model_type,
            input_channels=self.input_channels,
            board_size=self.board_size,
            conv_channels=self.conv_channels,
            use_dueling=self.use_dueling,
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
                # grad w accumulates over batch
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


def encode_env_state(env: BattleshipEnv, last_action: Optional[Coordinate]) -> Tuple[np.ndarray, List[int]]:
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
            grad_a = grad_out_full
            mean_grad_a = np.mean(grad_a, axis=1, keepdims=True)
            grad_a = grad_a - mean_grad_a
            grad_h2_a = grad_a @ q_net.wa.T
            grad_wa = cache["h2"].T @ grad_a
            grad_ba = np.sum(grad_a, axis=0, keepdims=True)

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


def run_dqn_training(cfg: TrainConfig, dqn_cfg: DQNConfig) -> dict:
    env = BattleshipEnv(
        board_size=cfg.board_size,
        seed=cfg.seed,
        ships=cfg.ships or DEFAULT_SHIPS,
        allow_adjacent=cfg.allow_adjacent,
        reward_step_base=cfg.reward_step_base,
        reward_step_decay=cfg.reward_step_decay,
        reward_step_cap=cfg.reward_step_cap,
        reward_hit=cfg.reward_hit,
        reward_miss=cfg.reward_miss,
        reward_sink_mult=cfg.reward_sink_mult,
        reward_win_max=cfg.reward_win_max,
        reward_win_decay_k=cfg.reward_win_decay_k,
        reward_loss=cfg.reward_loss,
        reward_perfect_move=cfg.reward_perfect_move,
    )
    channels = 6  # encoder channels when include_hit_cluster=True, include_self=False
    input_dim = channels * cfg.board_size * cfg.board_size
    output_dim = cfg.board_size * cfg.board_size
    q_net = NumpyDQN(
        input_dim,
        output_dim,
        hidden=dqn_cfg.hidden,
        model=dqn_cfg.model,
        input_channels=channels,
        board_size=cfg.board_size,
        conv_channels=dqn_cfg.conv_channels,
        use_dueling=dqn_cfg.use_dueling,
    )
    target_net = q_net.copy()
    buffer = ReplayBuffer(dqn_cfg.buffer_size)

    epsilon = dqn_cfg.epsilon_start
    eps_min = dqn_cfg.epsilon_min
    eps_decay = (dqn_cfg.epsilon_start - eps_min) / max(1, dqn_cfg.epsilon_decay)

    for episode in range(1, dqn_cfg.max_episodes + 1):
        env.reset()
        done = False
        last_action: Optional[Coordinate] = None
        while not done:
            grid, mask = encode_env_state(env, last_action)
            action = select_action(q_net, grid, mask, epsilon)
            reward, done = env.step(action)
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

            if epsilon > eps_min:
                epsilon = max(eps_min, epsilon - eps_decay)
            last_action = action

        if episode % dqn_cfg.target_update == 0:
            target_net = q_net.copy()
        if episode % 500 == 0:
            print(f"[dqn] episode={episode} epsilon={epsilon:.3f}", file=sys.stderr, flush=True)

    artifact_name = cfg.artifact_name
    if not artifact_name.endswith(".npz"):
        artifact_name = f"{artifact_name}.npz"
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
    }
    manifest_path = cfg.output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return {"artifact": str(artifact_path), "manifest": str(manifest_path), "hash": digest, "version": cfg.version}


def main() -> None:
    cfg = TrainConfig.from_env()
    dqn_cfg = DQNConfig.from_env()
    result = run_dqn_training(cfg, dqn_cfg)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

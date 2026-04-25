#!/usr/bin/env python
"""
Quick-and-dirty plot for DQN self-play metrics CSV.
By default, loads the latest dqn_selfplay_metrics-<timestamp>.csv in ./artifacts.
Override with --file <path>.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def find_latest_metrics(base: Path) -> Path | None:
    files = sorted(base.glob("dqn_selfplay_metrics-*.csv"))
    return files[-1] if files else None


def derive_output_name(csv_path: Path, output: str | None) -> Path | None:
    if output:
        return Path(output).expanduser()
    stem = csv_path.stem.replace("metrics", "plot")
    return csv_path.with_name(f"{stem}.png")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot DQN self-play metrics")
    parser.add_argument(
        "--file",
        type=str,
        help="Path to metrics CSV (defaults to latest dqn_selfplay_metrics-*.csv in ./artifacts)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Optional path to save the plot (png). If omitted, shows interactively.",
    )
    args = parser.parse_args()

    if args.file:
        path = Path(args.file).expanduser()
    else:
        path = find_latest_metrics(Path("artifacts"))
        if not path:
            raise SystemExit(
                "No metrics file found. Provide --file or ensure artifacts/dqn_selfplay_metrics-*.csv exists."
            )

    df = pd.read_csv(path)
    out_path = derive_output_name(path, args.output)
    # Keep only relevant phases and coerce numerics
    train_df = df[df["phase"] == "train"].copy()
    eval_df = df[df["phase"].isin(["baseline_eval", "selfplay_eval"])].copy()
    for col in ("outcome", "p1_moves", "p2_moves", "episode"):
        if col in eval_df.columns:
            eval_df[col] = pd.to_numeric(eval_df[col], errors="coerce")
    for col in ("epsilon", "episode"):
        if col in train_df.columns:
            train_df[col] = pd.to_numeric(train_df[col], errors="coerce")

    fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=False)

    if not train_df.empty:
        axes[0].plot(train_df["episode"], train_df["epsilon"], label="epsilon", color="tab:orange")
        axes[0].set_ylabel("Epsilon")
        axes[0].set_title(f"Training epsilon (episodes={train_df['episode'].max()})")
        axes[0].grid(True, alpha=0.3)

    if not eval_df.empty:
        for phase, g in eval_df.groupby("phase"):
            g = g.sort_values("episode")
            x = g["episode"] if g["episode"].notna().any() else g.index
            y = g["outcome"].rolling(window=50, min_periods=1).mean()
            axes[1].plot(x, y, label=f"{phase} rolling win")
        axes[1].set_ylabel("Rolling win rate")
        axes[1].set_title("Eval rolling win rate (window=50)")
        axes[1].grid(True, alpha=0.3)
        axes[1].legend()

    if not eval_df.empty:
        axes[2].plot(eval_df.index, eval_df["p1_moves"], ".", alpha=0.3, label="p1_moves")
        axes[2].plot(eval_df.index, eval_df["p2_moves"], ".", alpha=0.3, label="p2_moves")
        axes[2].set_ylabel("Moves")
        axes[2].set_title("Eval moves per game")
        axes[2].grid(True, alpha=0.3)
        axes[2].legend()

    axes[-1].set_xlabel("Index / Episode")
    fig.tight_layout()

    if out_path:
        fig.savefig(out_path, dpi=150)
        print(f"Saved plot to {out_path}")
    else:
        plt.show()


if __name__ == "__main__":
    main()

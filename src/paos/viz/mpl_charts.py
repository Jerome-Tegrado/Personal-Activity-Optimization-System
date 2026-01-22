from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def save_activity_trend_png(df: pd.DataFrame, path: Path) -> None:
    d = df.sort_values("date").copy()
    plt.figure()
    plt.plot(d["date"], d["activity_level"], marker="o")
    plt.title("Activity Level Over Time")
    plt.xlabel("Date")
    plt.ylabel("Activity Level (0–100)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=150)
    plt.close()


def save_status_counts_png(df: pd.DataFrame, path: Path) -> None:
    counts = df["lifestyle_status"].value_counts()
    plt.figure()
    counts.plot(kind="bar")
    plt.title("Lifestyle Status Counts")
    plt.xlabel("Lifestyle Status")
    plt.ylabel("Days")
    plt.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=150)
    plt.close()


def save_activity_vs_energy_png(df: pd.DataFrame, path: Path) -> None:
    plt.figure()
    plt.scatter(df["activity_level"], df["energy_focus"])
    plt.title("Activity Level vs Energy/Focus")
    plt.xlabel("Activity Level (0–100)")
    plt.ylabel("Energy/Focus (1–5)")
    plt.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=150)
    plt.close()

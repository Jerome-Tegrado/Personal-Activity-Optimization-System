from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ExperimentEffectRow:
    experiment: str
    metric: str
    n_control: int
    n_treatment: int
    control_mean: float
    treatment_mean: float
    delta: float
    delta_ci_low: float
    delta_ci_high: float
    n_boot: int


def _coerce_bool_phase(s: pd.Series) -> pd.Series:
    """
    Normalize phases to lower-case strings; caller should filter control/treatment.
    """
    return s.astype(str).str.strip().str.lower()


def _bootstrap_delta_ci(
    control_vals: np.ndarray,
    treat_vals: np.ndarray,
    n_boot: int = 2000,
    ci: float = 0.95,
    seed: int = 42,
) -> tuple[float, float]:
    """
    Bootstrap CI for delta = mean(treat) - mean(control).
    Returns (low, high). Requires at least 2 samples per group.
    """
    if len(control_vals) < 2 or len(treat_vals) < 2:
        return (float("nan"), float("nan"))
    if n_boot <= 0:
        return (float("nan"), float("nan"))
    if not (0.0 < ci < 1.0):
        raise ValueError("ci must be between 0 and 1 (exclusive).")

    rng = np.random.default_rng(seed)

    deltas = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        c = rng.choice(control_vals, size=len(control_vals), replace=True)
        t = rng.choice(treat_vals, size=len(treat_vals), replace=True)
        deltas[i] = float(np.mean(t) - np.mean(c))

    alpha = (1.0 - ci) / 2.0
    low = float(np.quantile(deltas, alpha))
    high = float(np.quantile(deltas, 1.0 - alpha))
    return (low, high)


def compute_experiment_effects(
    df: pd.DataFrame,
    experiment_col: str = "experiment",
    phase_col: str = "experiment_phase",
    metrics: tuple[str, ...] = ("activity_level", "energy_focus"),
    control_label: str = "control",
    treatment_label: str = "treatment",
    add_ci: bool = True,
    n_boot: int = 2000,
    ci: float = 0.95,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Compute treatment vs control mean differences for each experiment.

    Expects df to have:
      - experiment_col (string)
      - phase_col (control/treatment)
      - metric columns (numeric or coercible)

    Returns a tidy DataFrame with rows:
      experiment, metric, n_control, n_treatment, control_mean, treatment_mean, delta,
      delta_ci_low, delta_ci_high, n_boot

    CI behavior:
      - If add_ci=False -> CI columns still exist but are NaN and n_boot=0
      - If either group has <2 samples -> CI columns are NaN
    """
    base_cols = [
        "experiment",
        "metric",
        "n_control",
        "n_treatment",
        "control_mean",
        "treatment_mean",
        "delta",
        "delta_ci_low",
        "delta_ci_high",
        "n_boot",
    ]

    if df is None or df.empty:
        return pd.DataFrame(columns=base_cols)

    if experiment_col not in df.columns:
        raise ValueError(f"Missing required column: {experiment_col}")
    if phase_col not in df.columns:
        raise ValueError(f"Missing required column: {phase_col}")

    missing_metrics = [m for m in metrics if m not in df.columns]
    if missing_metrics:
        raise ValueError(f"Missing required metric columns: {missing_metrics}")

    work = df.copy()
    work[experiment_col] = work[experiment_col].astype("string")
    work[phase_col] = _coerce_bool_phase(work[phase_col])

    # Only keep rows with experiment name and valid phase
    work = work.dropna(subset=[experiment_col, phase_col])
    work = work[work[experiment_col].astype(str).str.len() > 0]

    # Limit to control/treatment rows
    work = work[work[phase_col].isin([control_label, treatment_label])]

    if work.empty:
        return pd.DataFrame(columns=base_cols)

    rows: list[dict[str, object]] = []

    for exp, g in work.groupby(experiment_col, dropna=True):
        g_control = g[g[phase_col] == control_label]
        g_treat = g[g[phase_col] == treatment_label]

        for metric in metrics:
            control_vals = pd.to_numeric(g_control[metric], errors="coerce").dropna().to_numpy(dtype=float)
            treat_vals = pd.to_numeric(g_treat[metric], errors="coerce").dropna().to_numpy(dtype=float)

            n_control = int(len(control_vals))
            n_treatment = int(len(treat_vals))

            control_mean = float(np.mean(control_vals)) if n_control else float("nan")
            treatment_mean = float(np.mean(treat_vals)) if n_treatment else float("nan")

            delta = treatment_mean - control_mean

            if add_ci and n_control >= 2 and n_treatment >= 2:
                ci_low, ci_high = _bootstrap_delta_ci(
                    control_vals,
                    treat_vals,
                    n_boot=n_boot,
                    ci=ci,
                    seed=seed,
                )
                boot_used = int(n_boot)
            else:
                ci_low, ci_high = float("nan"), float("nan")
                boot_used = 0

            rows.append(
                {
                    "experiment": str(exp),
                    "metric": metric,
                    "n_control": n_control,
                    "n_treatment": n_treatment,
                    "control_mean": control_mean,
                    "treatment_mean": treatment_mean,
                    "delta": delta,
                    "delta_ci_low": ci_low,
                    "delta_ci_high": ci_high,
                    "n_boot": boot_used,
                }
            )

    return pd.DataFrame(rows, columns=base_cols)

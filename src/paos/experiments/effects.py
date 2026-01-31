from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

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


def _coerce_bool_phase(s: pd.Series) -> pd.Series:
    """
    Normalize phases to lower-case strings; caller should filter control/treatment.
    """
    return s.astype(str).str.strip().str.lower()


def _mean_safe(series: pd.Series) -> float:
    x = pd.to_numeric(series, errors="coerce").dropna()
    if len(x) == 0:
        return float("nan")
    return float(x.mean())


def compute_experiment_effects(
    df: pd.DataFrame,
    experiment_col: str = "experiment",
    phase_col: str = "experiment_phase",
    metrics: tuple[str, ...] = ("activity_level", "energy_focus"),
    control_label: str = "control",
    treatment_label: str = "treatment",
) -> pd.DataFrame:
    """
    Compute treatment vs control mean differences for each experiment.

    Expects df to have:
      - experiment_col (string)
      - phase_col (control/treatment)
      - metric columns (numeric or coercible)

    Returns a tidy DataFrame with rows:
      experiment, metric, n_control, n_treatment, control_mean, treatment_mean, delta
    """
    if df is None or df.empty:
        return pd.DataFrame(
            columns=[
                "experiment",
                "metric",
                "n_control",
                "n_treatment",
                "control_mean",
                "treatment_mean",
                "delta",
            ]
        )

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

    rows: list[dict[str, object]] = []

    if work.empty:
        return pd.DataFrame(
            columns=[
                "experiment",
                "metric",
                "n_control",
                "n_treatment",
                "control_mean",
                "treatment_mean",
                "delta",
            ]
        )

    for exp, g in work.groupby(experiment_col, dropna=True):
        g_control = g[g[phase_col] == control_label]
        g_treat = g[g[phase_col] == treatment_label]

        for metric in metrics:
            control_vals = pd.to_numeric(g_control[metric], errors="coerce").dropna()
            treat_vals = pd.to_numeric(g_treat[metric], errors="coerce").dropna()

            n_control = int(len(control_vals))
            n_treatment = int(len(treat_vals))

            control_mean = float(control_vals.mean()) if n_control else float("nan")
            treatment_mean = float(treat_vals.mean()) if n_treatment else float("nan")

            delta = treatment_mean - control_mean

            rows.append(
                {
                    "experiment": str(exp),
                    "metric": metric,
                    "n_control": n_control,
                    "n_treatment": n_treatment,
                    "control_mean": control_mean,
                    "treatment_mean": treatment_mean,
                    "delta": delta,
                }
            )

    return pd.DataFrame(rows)

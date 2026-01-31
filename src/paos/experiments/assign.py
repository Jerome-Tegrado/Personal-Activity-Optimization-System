from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from .spec import load_experiment_spec_csv


def assign_experiments_to_days(
    df: pd.DataFrame,
    spec_csv_path: str | Path,
    date_col: str = "date",
    out_experiment_col: str = "experiment",
    out_phase_col: str = "experiment_phase",
    out_label_col: str = "experiment_label",
) -> pd.DataFrame:
    """
    Assign each day in df to an experiment window based on a CSV spec.

    - If a day matches multiple windows, the LAST matching row in the spec wins
      (so you can override earlier rows by placing later ones at the bottom).
    - If a day matches no window, experiment columns remain NA.

    Returns a copy of df with added columns.
    """
    out = df.copy()

    if date_col not in out.columns:
        raise ValueError(f"Expected '{date_col}' column in daily dataframe.")

    # Normalize day dates
    out[date_col] = pd.to_datetime(out[date_col], errors="coerce").dt.normalize()
    out = out.dropna(subset=[date_col]).reset_index(drop=True)

    spec = load_experiment_spec_csv(spec_csv_path)

    # Initialize output cols
    out[out_experiment_col] = pd.NA
    out[out_phase_col] = pd.NA
    out[out_label_col] = pd.NA

    # Apply each spec row; later rows override earlier ones
    for _, r in spec.iterrows():
        exp = r["experiment"]
        phase = r["phase"]
        label = r.get("label", pd.NA)

        mask = (out[date_col] >= r["start_date"]) & (out[date_col] <= r["end_date"])
        if mask.any():
            out.loc[mask, out_experiment_col] = exp
            out.loc[mask, out_phase_col] = phase
            out.loc[mask, out_label_col] = label

    return out

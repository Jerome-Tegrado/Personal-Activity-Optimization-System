from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class ExperimentSpec:
    """
    A single experiment window definition.

    Dates are inclusive: start_date <= day <= end_date.
    """
    experiment: str
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    phase: str  # "control" or "treatment" (or any label you want)
    label: Optional[str] = None


def load_experiment_spec_csv(path: str | Path) -> pd.DataFrame:
    """
    Load experiments from a CSV spec file.

    Required columns:
      - experiment
      - start_date
      - end_date
      - phase

    Optional:
      - label

    Returns a DataFrame with normalized columns and datetime start/end.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Experiment spec file not found: {path}")

    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]

    required = ["experiment", "start_date", "end_date", "phase"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required experiment spec columns: {missing}")

    df["experiment"] = df["experiment"].astype(str).str.strip()
    df["phase"] = df["phase"].astype(str).str.strip().str.lower()

    # Normalize dates
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce").dt.normalize()
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce").dt.normalize()

    if df["start_date"].isna().any() or df["end_date"].isna().any():
        bad = df[df["start_date"].isna() | df["end_date"].isna()].head(5)
        raise ValueError(
            "Invalid start_date/end_date in experiment spec. "
            f"Example bad rows: {bad.to_dict(orient='records')}"
        )

    # Ensure start <= end
    bad_range = df[df["start_date"] > df["end_date"]]
    if not bad_range.empty:
        raise ValueError(
            "Found experiment spec rows where start_date > end_date. "
            f"Example: {bad_range.head(5).to_dict(orient='records')}"
        )

    if "label" in df.columns:
        df["label"] = df["label"].astype("string")
    else:
        df["label"] = pd.NA

    return df

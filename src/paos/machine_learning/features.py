from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class EnergyFeatureConfig:
    """
    Configuration for feature generation.

    Notes on leakage:
    - Lag and rolling features are computed using shift(1),
      so they only use information available before the current day.
    """
    date_col: str = "date"
    target_col: str = "energy_focus"
    steps_col: str = "steps"
    step_points_col: str = "step_points"
    exercise_points_col: str = "exercise_points"
    activity_level_col: str = "activity_level"

    rolling_window_days: int = 7


def _require_cols(df: pd.DataFrame, cols: Iterable[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {missing}. Present: {list(df.columns)}")


def build_energy_features(
    df: pd.DataFrame,
    config: EnergyFeatureConfig | None = None,
) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """
    Build leakage-safe features to predict energy_focus.

    Parameters
    ----------
    df:
        Daily data (ideally enriched). Must include at least:
        - date
        - energy_focus
        - steps
        - activity_level OR (step_points + exercise_points)
    config:
        Optional feature config.

    Returns
    -------
    X_df:
        Feature matrix as a DataFrame.
    y:
        Target series aligned to X_df.
    feature_names:
        List of feature column names in order.
    """
    cfg = config or EnergyFeatureConfig()

    _require_cols(df, [cfg.date_col, cfg.target_col, cfg.steps_col])

    work = df.copy()

    # Parse/sort date
    work[cfg.date_col] = pd.to_datetime(work[cfg.date_col], errors="coerce")
    if work[cfg.date_col].isna().any():
        bad = work[work[cfg.date_col].isna()]
        raise ValueError(
            f"Found invalid dates in column '{cfg.date_col}'. "
            f"Example invalid rows (up to 3): {bad.head(3).to_dict(orient='records')}"
        )
    work = work.sort_values(cfg.date_col).reset_index(drop=True)

    # Ensure activity_level exists (compute if possible)
    if cfg.activity_level_col not in work.columns:
        if cfg.step_points_col in work.columns and cfg.exercise_points_col in work.columns:
            work[cfg.activity_level_col] = (
                pd.to_numeric(work[cfg.step_points_col], errors="coerce").fillna(0).astype(float)
                + pd.to_numeric(work[cfg.exercise_points_col], errors="coerce").fillna(0).astype(float)
            )
        else:
            raise ValueError(
                "Missing 'activity_level' and cannot compute it because "
                "'step_points' and/or 'exercise_points' are missing."
            )

    # Numeric hygiene
    work[cfg.steps_col] = pd.to_numeric(work[cfg.steps_col], errors="coerce")
    work[cfg.activity_level_col] = pd.to_numeric(work[cfg.activity_level_col], errors="coerce")

    # Safe context features
    work["day_of_week"] = work[cfg.date_col].dt.dayofweek.astype(int)  # 0=Mon .. 6=Sun
    work["is_weekend"] = (work["day_of_week"] >= 5).astype(int)

    # Optional score components if present
    if cfg.step_points_col in work.columns:
        work[cfg.step_points_col] = pd.to_numeric(work[cfg.step_points_col], errors="coerce")
    if cfg.exercise_points_col in work.columns:
        work[cfg.exercise_points_col] = pd.to_numeric(work[cfg.exercise_points_col], errors="coerce")

    # Leakage-safe time-series features (shifted)
    work["activity_level_lag_1"] = work[cfg.activity_level_col].shift(1)
    work["activity_level_rollmean_7"] = (
        work[cfg.activity_level_col]
        .shift(1)
        .rolling(window=cfg.rolling_window_days, min_periods=1)
        .mean()
    )

    # Feature list (keep deterministic order)
    feature_names: List[str] = [
        cfg.steps_col,
        cfg.activity_level_col,
        "day_of_week",
        "is_weekend",
        "activity_level_lag_1",
        "activity_level_rollmean_7",
    ]

    # Include points if available (helps explainability)
    if cfg.step_points_col in work.columns:
        feature_names.insert(1, cfg.step_points_col)
    if cfg.exercise_points_col in work.columns:
        insert_at = 2 if cfg.step_points_col in work.columns else 1
        feature_names.insert(insert_at, cfg.exercise_points_col)

    # Build X/y and drop rows with NaNs (mostly first row due to lag)
    X_df = work[feature_names].copy()
    y = pd.to_numeric(work[cfg.target_col], errors="coerce")

    valid_mask = (~y.isna()) & (~X_df.isna().any(axis=1))
    X_df = X_df.loc[valid_mask].reset_index(drop=True)
    y = y.loc[valid_mask].reset_index(drop=True)

    return X_df, y, feature_names

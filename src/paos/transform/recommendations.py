from __future__ import annotations

import math
from typing import Optional

import pandas as pd


def _is_missing(x: object) -> bool:
    try:
        return x is None or (isinstance(x, float) and math.isnan(x))
    except Exception:
        return x is None


def base_recommendation(activity_level: Optional[float]) -> str:
    """
    Baseline recommendation based on activity_level bands.
    Kept simple and explainable on purpose.
    """
    if _is_missing(activity_level):
        return "Log activity consistently so PAOS can generate recommendations."

    level = float(activity_level)

    if level <= 25:
        return "Add a 20–30 min walk to increase activity and energy."
    if level <= 50:
        return "Include a moderate session to reach Active status."
    if level <= 75:
        return "Maintain routine; add variety (strength/mobility) to avoid plateaus."
    return "Excellent — prioritize recovery (sleep, hydration)."


def recommend(activity_level: Optional[float], energy_focus: Optional[float]) -> str:
    """
    Returns a daily recommendation string.

    V2 trend-aware rule #1 (small MVP):
    - High activity + low energy => recovery check.
    """
    msg = base_recommendation(activity_level)

    if _is_missing(activity_level) or _is_missing(energy_focus):
        return msg

    level = float(activity_level)
    ef = float(energy_focus)

    # Rule #1: high activity + low energy => recovery nudge
    if level >= 70 and ef <= 2:
        msg += " High effort + low energy — prioritize recovery (sleep, hydration, lighter training)."

    return msg


def recommend_series(df: pd.DataFrame) -> pd.Series:
    """
    Generate recommendations for a whole dataframe, enabling simple trend rules.

    Required columns:
      - activity_level
    Optional columns:
      - energy_focus

    Trend-aware rule #2:
      - If the last 3 *consecutive days* show a strict activity downtrend
        (d-2 > d-1 > d), append a momentum nudge for day d.
    """
    if "activity_level" not in df.columns:
        raise ValueError("recommend_series requires an 'activity_level' column")

    energy_col_exists = "energy_focus" in df.columns

    out = df.copy()

    if "date" in out.columns:
        # best effort sorting by date
        out = out.sort_values("date")

    # Base recommendations row-by-row (rule #1 lives inside recommend())
    recs = out.apply(
        lambda r: recommend(
            r.get("activity_level"),
            r.get("energy_focus") if energy_col_exists else None,
        ),
        axis=1,
    ).astype(str)

    # Rule #2: 3-day downtrend in activity_level
    a = pd.to_numeric(out["activity_level"], errors="coerce")

    # Strict downtrend across the last 3 rows (as ordered above)
    downtrend_today = (a.shift(2) > a.shift(1)) & (a.shift(1) > a)

    # If date exists, require consecutive days (no gaps) so we don't misfire
    if "date" in out.columns:
        d = pd.to_datetime(out["date"], errors="coerce")
        consecutive = (d.diff() == pd.Timedelta(days=1)) & (d.diff().shift(1) == pd.Timedelta(days=1))
        downtrend_today = downtrend_today & consecutive

    nudge = " Activity has dipped for 3 days — do a small reset (10–20 min walk) to rebuild momentum."
    recs = recs.where(~downtrend_today, recs + nudge)

    return recs

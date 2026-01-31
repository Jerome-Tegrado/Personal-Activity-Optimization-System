from __future__ import annotations

import pandas as pd

from paos.config import DURATION_BANDS, HR_MULTIPLIERS, STATUS_BANDS, STEP_BANDS
from paos.transform.recommendations import recommend_series


def score_steps(steps: float) -> int:
    if pd.isna(steps):
        return 0
    s = int(steps)
    for lo, hi, pts in STEP_BANDS:
        if lo <= s <= hi:
            return int(pts)
    return 0


def base_duration_points(minutes: float) -> int:
    if pd.isna(minutes):
        return 0
    m = int(minutes)
    for lo, hi, pts in DURATION_BANDS:
        if lo <= m <= hi:
            return int(pts)
    return 0


def score_exercise(did_exercise: object, minutes: object, zone: object) -> int:
    """
    did_exercise can be bool or a string like "Yes"/"No".
    minutes/zone may be missing (NA) on rest days or steps-only logs.
    """
    flag = str(did_exercise).strip().lower() in {"yes", "true", "1"}
    if not flag:
        return 0

    base = base_duration_points(minutes)
    z = str(zone).strip().lower() if zone is not None and not pd.isna(zone) else "unknown"
    mult = HR_MULTIPLIERS.get(z, HR_MULTIPLIERS["unknown"])
    return int(min(50, int(base * mult)))


def classify_status(activity_level: int) -> str:
    for lo, hi, label in STATUS_BANDS:
        if lo <= activity_level <= hi:
            return label
    return "Unknown"


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Ensure optional columns exist for steps-only logs
    for col in ["exercise_type", "exercise_minutes", "heart_rate_zone", "notes"]:
        if col not in out.columns:
            out[col] = pd.NA

    out["step_points"] = out["steps"].apply(score_steps)

    out["exercise_points"] = out.apply(
        lambda r: score_exercise(
            r.get("did_exercise"),
            r.get("exercise_minutes"),
            r.get("heart_rate_zone"),
        ),
        axis=1,
    )

    out["activity_level"] = (out["step_points"] + out["exercise_points"]).clip(0, 100).astype(int)
    out["lifestyle_status"] = out["activity_level"].apply(classify_status)

    # V2 trend-aware recommendations (includes 3-day downtrend rule)
    out["recommendation"] = recommend_series(out)

    return out

from __future__ import annotations

import math
from typing import Optional

import pandas as pd


# ---- Thresholds / bands (easy to tweak later) ----
SEDENTARY_MAX = 25
HIGH_ACTIVITY_MIN = 70
LOW_ENERGY_MAX = 2

# Trend thresholds
BOUNCE_BACK_DELTA = 20  # +20 activity vs yesterday (consecutive day) => praise


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
    Single-day recommendation logic.

    Rule #1:
      - High activity + low energy => recovery nudge.
    """
    msg = base_recommendation(activity_level)

    if _is_missing(activity_level) or _is_missing(energy_focus):
        return msg

    level = float(activity_level)
    ef = float(energy_focus)

    if level >= HIGH_ACTIVITY_MIN and ef <= LOW_ENERGY_MAX:
        msg += " High effort + low energy — prioritize recovery (sleep, hydration, lighter training)."

    return msg


def recommend_series(df: pd.DataFrame) -> pd.Series:
    """
    Generate recommendations for a dataframe, enabling simple trend-aware rules.

    Required columns:
      - activity_level
    Optional columns:
      - energy_focus
      - date  (if present, rules require *consecutive days* to avoid false triggers)

    Trend rules applied here:
      Rule #2: strict 3-day consecutive downtrend in activity_level => momentum nudge
      Rule #3: 2+ consecutive sedentary days (<= 25) => streak-break nudge
      Rule #4: weekday dip (Mon–Fri sedentary) => scheduling nudge
      Rule #5: weekend recovery (Sat/Sun + high activity + low energy) => weekend-specific recovery nudge
      Rule #6: 3+ consecutive sedentary days => stronger escalation nudge
      Rule #7: bounce-back (consecutive day + >= +20 activity) => praise nudge
    """
    if "activity_level" not in df.columns:
        raise ValueError("recommend_series requires an 'activity_level' column")

    out = df.copy()

    # Best effort sorting by date so "trend" means time order
    if "date" in out.columns:
        out = out.sort_values("date")

    energy_col_exists = "energy_focus" in out.columns

    # Base per-row recommendations (Rule #1 lives inside recommend())
    recs = out.apply(
        lambda r: recommend(
            r.get("activity_level"),
            r.get("energy_focus") if energy_col_exists else None,
        ),
        axis=1,
    ).astype(str)

    a = pd.to_numeric(out["activity_level"], errors="coerce")

    has_date = "date" in out.columns
    if has_date:
        d = pd.to_datetime(out["date"], errors="coerce")
    else:
        d = None

    # Helper: consecutive-day mask for "today" and "yesterday"
    if has_date:
        consec_1 = d.diff() == pd.Timedelta(days=1)
        consec_2 = consec_1 & (d.diff().shift(1) == pd.Timedelta(days=1))
    else:
        consec_1 = pd.Series(True, index=out.index)
        consec_2 = pd.Series(True, index=out.index)

    # -------------------------
    # Rule #2: 3-day downtrend
    # -------------------------
    downtrend_today = (a.shift(2) > a.shift(1)) & (a.shift(1) > a) & consec_2
    downtrend_nudge = (
        " Activity has dipped for 3 days — do a small reset (10–20 min walk) to rebuild momentum."
    )
    recs = recs.where(~downtrend_today, recs + downtrend_nudge)

    # ----------------------------------------
    # Rule #3: consecutive sedentary day streak
    # ----------------------------------------
    sedentary = a <= SEDENTARY_MAX
    sedentary_streak_2 = sedentary & sedentary.shift(1) & consec_1
    streak_2_nudge = (
        " Two sedentary days in a row — go for a tiny win today (10–15 min walk) to break the streak."
    )
    recs = recs.where(~sedentary_streak_2, recs + streak_2_nudge)

    # ----------------------------------------
    # Rule #6: 3-day sedentary streak escalation
    # ----------------------------------------
    sedentary_streak_3 = sedentary & sedentary.shift(1) & sedentary.shift(2) & consec_2
    streak_3_nudge = (
        " Three sedentary days in a row — make it easy: schedule a 20–30 min walk and remove friction (shoes ready, calendar block)."
    )
    recs = recs.where(~sedentary_streak_3, recs + streak_3_nudge)

    # -------------------------
    # Rule #4: weekday dip nudge
    # -------------------------
    if has_date:
        weekday = pd.to_datetime(out["date"], errors="coerce").dt.weekday  # Mon=0 .. Sun=6
        weekday_sedentary = (weekday <= 4) & (a <= SEDENTARY_MAX)
        weekday_nudge = (
            " Weekday dip detected — schedule a short walk (10–20 min) during a fixed slot (lunch/after work)."
        )
        recs = recs.where(~weekday_sedentary, recs + weekday_nudge)

    # -------------------------
    # Rule #5: weekend recovery
    # -------------------------
    if has_date and energy_col_exists:
        weekday = pd.to_datetime(out["date"], errors="coerce").dt.weekday  # Mon=0 .. Sun=6
        ef = pd.to_numeric(out["energy_focus"], errors="coerce")

        weekend = weekday >= 5  # Sat/Sun
        weekend_recovery = weekend & (a >= HIGH_ACTIVITY_MIN) & (ef <= LOW_ENERGY_MAX)

        weekend_msg = (
            " Weekend recovery tip — keep it light today (easy walk/mobility) and prioritize sleep."
        )
        recs = recs.where(~weekend_recovery, recs + weekend_msg)

    # -------------------------
    # Rule #7: bounce-back praise
    # -------------------------
    bounce_back = consec_1 & ((a - a.shift(1)) >= BOUNCE_BACK_DELTA)
    bounce_msg = " Nice bounce-back — great job increasing activity. Keep the streak going with something sustainable tomorrow."
    recs = recs.where(~bounce_back, recs + bounce_msg)

    return recs

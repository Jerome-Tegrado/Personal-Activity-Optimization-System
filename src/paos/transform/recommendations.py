from __future__ import annotations

from typing import Optional

import math


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

    V2 trend-aware rule (small MVP):
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

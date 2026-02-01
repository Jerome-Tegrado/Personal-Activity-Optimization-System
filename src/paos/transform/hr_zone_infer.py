from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class HRZoneInferConfig:
    """
    Configuration for HR zone inference.

    Default max_hr matches your current v1 estimate (220 - age 22 = 198).
    You can later move this to config.py when you're ready.
    """

    max_hr_bpm: int = 198


def _is_truthy_exercise_flag(val: object) -> bool:
    return str(val).strip().lower() in {"yes", "true", "1"}


def _normalize_zone(val: object) -> str:
    if val is None or pd.isna(val):
        return ""
    z = str(val).strip().lower()
    if z in {"light", "moderate", "intense", "peak", "unknown"}:
        return z
    return ""


def infer_zone_from_time_in_zone_row(row: pd.Series) -> Optional[str]:
    """
    Infer zone from time-in-zone minute columns:
      minutes_light, minutes_moderate, minutes_intense, minutes_peak

    Rule: pick the zone with the most minutes.
    Tie-breaker: pick higher intensity (peak > intense > moderate > light).
    If all missing/zero -> None.
    """
    cols = {
        "light": "minutes_light",
        "moderate": "minutes_moderate",
        "intense": "minutes_intense",
        "peak": "minutes_peak",
    }

    if not any(c in row.index for c in cols.values()):
        return None

    mins: dict[str, float] = {}
    any_present = False
    for zone, col in cols.items():
        if col in row.index:
            any_present = True
            v = pd.to_numeric(row.get(col), errors="coerce")
            mins[zone] = 0.0 if pd.isna(v) else float(v)
        else:
            mins[zone] = 0.0

    if not any_present:
        return None

    # If everything is 0 -> no inference
    if all(v <= 0 for v in mins.values()):
        return None

    # pick max minutes; tie-breaker = higher intensity
    intensity_rank = {"light": 1, "moderate": 2, "intense": 3, "peak": 4}
    best_zone = max(mins.keys(), key=lambda z: (mins[z], intensity_rank[z]))
    return best_zone


def infer_zone_from_avg_hr_bpm(avg_hr_bpm: object, cfg: HRZoneInferConfig) -> Optional[str]:
    """
    Infer zone from avg_hr_bpm using % of max HR bands:
      Light:    50-60%
      Moderate: 60-70%
      Intense:  70-85%
      Peak:     85-95%

    Returns None if invalid/outside reasonable range.
    """
    v = pd.to_numeric(avg_hr_bpm, errors="coerce")
    if pd.isna(v):
        return None

    bpm = float(v)
    if bpm <= 0:
        return None

    max_hr = float(cfg.max_hr_bpm)
    if max_hr <= 0:
        return None

    pct = bpm / max_hr

    # basic sanity bounds (optional guard)
    if pct < 0.40 or pct > 1.10:
        return None

    if 0.50 <= pct < 0.60:
        return "light"
    if 0.60 <= pct < 0.70:
        return "moderate"
    if 0.70 <= pct < 0.85:
        return "intense"
    if 0.85 <= pct <= 0.95:
        return "peak"

    # between 0.95 and 1.10 or 0.40-0.50: treat as unknown rather than None
    return "unknown"


def infer_missing_heart_rate_zone(
    df: pd.DataFrame,
    cfg: HRZoneInferConfig | None = None,
) -> pd.DataFrame:
    """
    Fill heart_rate_zone when:
      - did_exercise is truthy
      - heart_rate_zone is missing/blank
      - optional HR columns exist: time-in-zone minutes OR avg_hr_bpm

    Does NOT overwrite existing heart_rate_zone.
    """
    cfg = cfg or HRZoneInferConfig()
    out = df.copy()

    # Ensure column exists
    if "heart_rate_zone" not in out.columns:
        out["heart_rate_zone"] = pd.NA

    # Normalize existing zone values (keep only allowed; others -> blank)
    out["heart_rate_zone"] = out["heart_rate_zone"].apply(_normalize_zone)

    def _infer_row(row: pd.Series) -> str:
        # only infer on exercise days
        if not _is_truthy_exercise_flag(row.get("did_exercise")):
            return row.get("heart_rate_zone") or ""

        # don't overwrite if already provided
        existing = _normalize_zone(row.get("heart_rate_zone"))
        if existing:
            return existing

        # Prefer time-in-zone if available
        z_tiz = infer_zone_from_time_in_zone_row(row)
        if z_tiz is not None:
            return z_tiz

        # Else try avg HR
        if "avg_hr_bpm" in row.index:
            z_hr = infer_zone_from_avg_hr_bpm(row.get("avg_hr_bpm"), cfg)
            if z_hr is not None:
                return z_hr

        return "unknown"

    out["heart_rate_zone"] = out.apply(_infer_row, axis=1)

    # Convert empty strings back to NA to match your style
    out.loc[out["heart_rate_zone"] == "", "heart_rate_zone"] = pd.NA
    return out

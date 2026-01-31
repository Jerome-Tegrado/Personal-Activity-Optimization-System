from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

import pandas as pd

from .redact import RedactConfig, redact_dataframe
from .types import Insight, InsightSeverity


@dataclass(frozen=True)
class InsightEngineConfig:
    """
    Configuration for generating privacy-safe insights.

    - week_mode: if True, bucket by ISO week (requires date column).
    - min_days: minimum rows required to produce insights.
    """
    week_mode: bool = True
    min_days: int = 7
    date_col: str = "date"
    activity_col: str = "activity_level"
    energy_col: str = "energy_focus"
    did_exercise_col: str = "did_exercise"


def _safe_bool_series(s: pd.Series) -> pd.Series:
    # supports bool, "Yes"/"No", "true"/"false", etc.
    return s.astype(str).str.strip().str.lower().isin({"yes", "true", "1"})


def generate_insights(df: pd.DataFrame, cfg: InsightEngineConfig | None = None) -> List[Insight]:
    """
    Generate privacy-safe insights from a PAOS enriched dataframe.

    Produces only aggregate/statistical statements (no notes, no exact dates by default).
    """
    cfg = cfg or InsightEngineConfig()

    if df is None or df.empty:
        return [
            Insight(
                key="no_data",
                title="No data available",
                message="No rows were found to generate insights.",
                severity=InsightSeverity.warn,
            )
        ]

    # Redact by default: drop notes; optionally bucket to week
    redact_cfg = RedactConfig(
        date_col=cfg.date_col,
        drop_notes=True,
        bucket_dates_to_week=cfg.week_mode,
        week_col="week",
    )
    safe = redact_dataframe(df, cfg=redact_cfg)

    insights: List[Insight] = []

    # Ensure numeric columns
    if cfg.activity_col in safe.columns:
        safe[cfg.activity_col] = pd.to_numeric(safe[cfg.activity_col], errors="coerce")
    if cfg.energy_col in safe.columns:
        safe[cfg.energy_col] = pd.to_numeric(safe[cfg.energy_col], errors="coerce")

    # Basic coverage check
    n_rows = len(safe)
    if n_rows < cfg.min_days:
        insights.append(
            Insight(
                key="low_coverage",
                title="Not enough days for strong insights",
                message=f"Only {n_rows} day(s) available. Add more logs to unlock weekly trends and correlations.",
                severity=InsightSeverity.warn,
                value=float(n_rows),
                unit="days",
            )
        )

    # -------- Insight 1: weekly averages (if week_mode) --------
    if cfg.week_mode and "week" in safe.columns and cfg.activity_col in safe.columns:
        weekly = safe.groupby("week", dropna=True)[cfg.activity_col].mean().dropna()
        if len(weekly) >= 1:
            last_week = str(weekly.index[-1])
            last_val = float(weekly.iloc[-1])
            insights.append(
                Insight(
                    key="weekly_activity_avg",
                    title="Weekly average activity",
                    message=f"Your average Activity Level for {last_week} is {last_val:.1f}.",
                    severity=InsightSeverity.info,
                    value=last_val,
                    unit="activity_level",
                    meta={"week": last_week},
                )
            )

    # -------- Insight 2: activity vs energy correlation --------
    if cfg.activity_col in safe.columns and cfg.energy_col in safe.columns:
        tmp = safe[[cfg.activity_col, cfg.energy_col]].dropna()
        if len(tmp) >= max(cfg.min_days, 5):
            corr = float(tmp[cfg.activity_col].corr(tmp[cfg.energy_col]))
            if pd.notna(corr):
                severity = InsightSeverity.info
                if abs(corr) >= 0.5:
                    severity = InsightSeverity.highlight
                insights.append(
                    Insight(
                        key="activity_energy_corr",
                        title="Activity vs Energy relationship",
                        message=f"Activity Level and Energy/Focus show a correlation of {corr:+.2f} (higher means they move together).",
                        severity=severity,
                        value=corr,
                        unit="corr",
                    )
                )

    # -------- Insight 3: exercise days vs rest days energy --------
    if cfg.did_exercise_col in safe.columns and cfg.energy_col in safe.columns:
        tmp = safe[[cfg.did_exercise_col, cfg.energy_col]].dropna()
        if len(tmp) >= max(cfg.min_days, 5):
            ex_flag = _safe_bool_series(tmp[cfg.did_exercise_col])
            ex_energy = tmp.loc[ex_flag, cfg.energy_col]
            rest_energy = tmp.loc[~ex_flag, cfg.energy_col]
            if len(ex_energy) >= 2 and len(rest_energy) >= 2:
                delta = float(ex_energy.mean() - rest_energy.mean())
                sev = InsightSeverity.info
                if abs(delta) >= 0.5:
                    sev = InsightSeverity.highlight
                insights.append(
                    Insight(
                        key="exercise_energy_delta",
                        title="Energy difference on exercise days",
                        message=f"On exercise days, your Energy/Focus is {delta:+.2f} points vs non-exercise days (average).",
                        severity=sev,
                        value=delta,
                        unit="energy_points",
                    )
                )

    if not insights:
        insights.append(
            Insight(
                key="no_insights",
                title="No insights generated yet",
                message="Data is present, but not enough valid rows/columns were available for insights. Keep logging consistently.",
                severity=InsightSeverity.warn,
            )
        )

    return insights

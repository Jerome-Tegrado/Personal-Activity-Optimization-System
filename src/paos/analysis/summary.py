from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from paos.insights.engine import InsightEngineConfig, generate_insights


def _prepare_df_with_dates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "date" not in out.columns:
        raise ValueError("Expected a 'date' column to write summaries.")
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date")
    return out


def _render_insights_md(df: pd.DataFrame) -> list[str]:
    """
    Render privacy-safe insights into markdown bullet points.
    Uses week bucketing by default (no exact dates).
    """
    insights = generate_insights(df, cfg=InsightEngineConfig(week_mode=True, min_days=7))
    lines: list[str] = []
    for ins in insights:
        lines.append(f"- **{ins.title}:** {ins.message}")
    return lines


def write_weekly_summary(
    df: pd.DataFrame, out_path: str | Path, week_end: Optional[str] = None
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = _prepare_df_with_dates(df)

    end = pd.to_datetime(week_end) if week_end else df["date"].max()
    start = end - pd.Timedelta(days=6)
    week = df[(df["date"] >= start) & (df["date"] <= end)].copy()

    days_logged = len(week)

    avg_activity = (
        round(float(pd.to_numeric(week.get("activity_level"), errors="coerce").mean()), 1)
        if days_logged and "activity_level" in week.columns
        else 0
    )
    avg_energy = (
        round(float(pd.to_numeric(week.get("energy_focus"), errors="coerce").mean()), 1)
        if days_logged and "energy_focus" in week.columns
        else 0
    )

    sedentary_days = (
        int((week["lifestyle_status"] == "Sedentary").sum())
        if days_logged and "lifestyle_status" in week.columns
        else 0
    )
    active_plus_days = (
        int((pd.to_numeric(week.get("activity_level"), errors="coerce") >= 51).sum())
        if days_logged and "activity_level" in week.columns
        else 0
    )

    corr = None
    if (
        days_logged >= 3
        and "activity_level" in week.columns
        and "energy_focus" in week.columns
        and week["activity_level"].nunique() > 1
        and week["energy_focus"].nunique() > 1
    ):
        corr = round(
            float(
                pd.to_numeric(week["activity_level"], errors="coerce").corr(
                    pd.to_numeric(week["energy_focus"], errors="coerce")
                )
            ),
            2,
        )

    md: list[str] = []
    md.append(f"# Week: {start.date()} → {end.date()}\n")
    md.append("## Overview")
    md.append(f"- **Days logged:** {days_logged}/7")
    md.append(f"- **Avg Activity Level:** {avg_activity}")
    md.append(f"- **Avg Energy/Focus:** {avg_energy}/5")
    md.append(f"- **Sedentary days:** {sedentary_days}")
    md.append(f"- **Active+ days:** {active_plus_days}\n")
    md.append("## Trends")
    md.append(f"- Correlation (Activity ↔ Energy): {corr if corr is not None else 'N/A'}\n")

    # v3 Section 3 Step 3: privacy-safe insights
    md.append("## Insights")
    md.extend(_render_insights_md(week))
    md.append("")

    out_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    return out_path


def write_monthly_summary(
    df: pd.DataFrame,
    out_path: str | Path,
    month: Optional[str] = None,
) -> Path:
    """
    Write a monthly summary markdown.

    month:
      - Optional month selector in "YYYY-MM" format.
      - If omitted, uses the month of the latest date in the data.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = _prepare_df_with_dates(df)

    if month:
        try:
            anchor = pd.to_datetime(f"{month}-01", format="%Y-%m-%d")
        except ValueError as e:
            raise ValueError("month must be in YYYY-MM format") from e
    else:
        anchor = df["date"].max()

    month_start = pd.Timestamp(year=int(anchor.year), month=int(anchor.month), day=1)
    month_end = month_start + pd.offsets.MonthEnd(1)

    m = df[(df["date"] >= month_start) & (df["date"] <= month_end)].copy()

    days_in_month = int(month_end.day)
    days_logged = len(m)

    activity = (
        pd.to_numeric(m.get("activity_level"), errors="coerce")
        if "activity_level" in m.columns
        else None
    )
    energy = (
        pd.to_numeric(m.get("energy_focus"), errors="coerce")
        if "energy_focus" in m.columns
        else None
    )

    avg_activity = round(float(activity.mean()), 1) if days_logged and activity is not None else 0
    avg_energy = round(float(energy.mean()), 1) if days_logged and energy is not None else 0

    sedentary_days = (
        int((m["lifestyle_status"] == "Sedentary").sum())
        if days_logged and "lifestyle_status" in m.columns
        else int((activity <= 25).sum()) if days_logged and activity is not None else 0
    )
    active_plus_days = int((activity >= 51).sum()) if days_logged and activity is not None else 0

    best_day = None
    if days_logged and activity is not None and activity.notna().any():
        idx = activity.idxmax()
        best_day = (m.loc[idx, "date"].date(), int(activity.loc[idx]))

    corr = None
    if (
        days_logged >= 7
        and activity is not None
        and energy is not None
        and activity.nunique() > 1
        and energy.nunique() > 1
    ):
        corr = round(float(activity.corr(energy)), 2)

    md: list[str] = []
    md.append(f"# Month: {month_start.date()} → {month_end.date()}\n")

    md.append("## Overview")
    md.append(f"- **Days logged:** {days_logged}/{days_in_month}")
    md.append(f"- **Avg Activity Level:** {avg_activity}")
    md.append(f"- **Avg Energy/Focus:** {avg_energy}/5")
    md.append(f"- **Sedentary days:** {sedentary_days}")
    md.append(f"- **Active+ days:** {active_plus_days}")

    if best_day is not None:
        d, score = best_day
        md.append(f"- **Best day (Activity Level):** {d} ({score})")

    md.append("\n## Trends")
    md.append(f"- Correlation (Activity ↔ Energy): {corr if corr is not None else 'N/A'}\n")

    # v3 Section 3 Step 3: privacy-safe insights
    md.append("## Insights")
    md.extend(_render_insights_md(m))
    md.append("")

    out_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    return out_path

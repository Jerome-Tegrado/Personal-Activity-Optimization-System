from __future__ import annotations

from pathlib import Path
from typing import Optional
import pandas as pd


def write_weekly_summary(df: pd.DataFrame, out_path: str | Path, week_end: Optional[str] = None) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")

    end = pd.to_datetime(week_end) if week_end else df["date"].max()
    start = end - pd.Timedelta(days=6)
    week = df[(df["date"] >= start) & (df["date"] <= end)].copy()

    days_logged = len(week)
    avg_activity = round(float(week["activity_level"].mean()), 1) if days_logged else 0
    avg_energy = round(float(week["energy_focus"].mean()), 1) if days_logged else 0
    sedentary_days = int((week["lifestyle_status"] == "Sedentary").sum()) if days_logged else 0
    active_plus_days = int((week["activity_level"] >= 51).sum()) if days_logged else 0

    corr = None
    if days_logged >= 3 and week["activity_level"].nunique() > 1 and week["energy_focus"].nunique() > 1:
        corr = round(float(week["activity_level"].corr(week["energy_focus"])), 2)

    md = []
    md.append(f"# Week: {start.date()} → {end.date()}\n")
    md.append("## Overview")
    md.append(f"- **Days logged:** {days_logged}/7")
    md.append(f"- **Avg Activity Level:** {avg_activity}")
    md.append(f"- **Avg Energy/Focus:** {avg_energy}/5")
    md.append(f"- **Sedentary days:** {sedentary_days}")
    md.append(f"- **Active+ days:** {active_plus_days}\n")
    md.append("## Trends")
    md.append(f"- Correlation (Activity ↔ Energy): {corr if corr is not None else 'N/A'}\n")

    out_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    return out_path

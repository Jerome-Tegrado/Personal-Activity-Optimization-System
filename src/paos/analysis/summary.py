from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from paos.insights.engine import InsightEngineConfig, generate_insights

# Experiment reporting is optional (skip if spec file missing)
from paos.experiments.assign import assign_experiments_to_days
from paos.experiments.effects import compute_experiment_effects

DEFAULT_EXPERIMENT_SPEC_PATH = Path("data/sample/experiments.csv")


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


def _fmt_num(x: object, decimals: int = 2) -> str:
    v = pd.to_numeric(x, errors="coerce")
    if pd.isna(v):
        return "N/A"
    return f"{float(v):.{decimals}f}"


def _render_experiments_md(
    week_df: pd.DataFrame,
    spec_path: Path = DEFAULT_EXPERIMENT_SPEC_PATH,
    n_boot: int = 500,
    ci: float = 0.95,
    seed: int = 42,
) -> list[str]:
    """
    Render experiment effect results into markdown.

    - Uses DEFAULT_EXPERIMENT_SPEC_PATH unless overridden later.
    - If the spec file doesn't exist, returns [] (silent skip).
    - Keeps output aggregate-only (no dates, no notes).
    """
    if week_df is None or week_df.empty:
        return []

    if not spec_path.exists():
        return []

    # Assign experiment/phase/label onto the week slice
    try:
        assigned = assign_experiments_to_days(week_df, spec_path, date_col="date")
    except Exception:
        # If anything goes wrong with spec parsing/assignment, skip section (non-fatal)
        return []

    # Only show if at least one day is part of an experiment
    if "experiment" not in assigned.columns or assigned["experiment"].isna().all():
        return []

    effects = compute_experiment_effects(
        assigned,
        experiment_col="experiment",
        phase_col="experiment_phase",
        metrics=("activity_level", "energy_focus"),
        add_ci=True,
        n_boot=n_boot,
        ci=ci,
        seed=seed,
    )

    if effects.empty:
        return [
            "- Not enough control/treatment coverage this week to estimate experiment effects.",
        ]

    lines: list[str] = []

    # Group by experiment and render metric rows
    for exp, g in effects.groupby("experiment", dropna=True):
        exp_name = str(exp)
        lines.append(f"### {exp_name}")

        # optional label (if present on assigned days, pick most common)
        label = None
        if "experiment_label" in assigned.columns:
            tmp = assigned.loc[assigned["experiment"] == exp_name, "experiment_label"].dropna()
            if len(tmp) > 0:
                # most frequent label for the week
                label = str(tmp.value_counts().index[0])
        if label:
            lines.append(f"- **Label:** {label}")

        for _, r in g.iterrows():
            metric = str(r.get("metric", ""))
            if metric == "activity_level":
                metric_name = "Activity Level"
            elif metric == "energy_focus":
                metric_name = "Energy/Focus"
            else:
                metric_name = metric

            delta = r.get("delta")
            control_mean = r.get("control_mean")
            treatment_mean = r.get("treatment_mean")
            n_control = int(r.get("n_control", 0) or 0)
            n_treat = int(r.get("n_treatment", 0) or 0)

            # CI (optional)
            ci_low = r.get("delta_ci_low")
            ci_high = r.get("delta_ci_high")
            boot_used = int(r.get("n_boot", 0) or 0)

            ci_txt = ""
            if boot_used > 0 and not pd.isna(ci_low) and not pd.isna(ci_high):
                ci_pct = int(round(ci * 100))
                ci_txt = f" (CI{ci_pct}% [{_fmt_num(ci_low)}, {_fmt_num(ci_high)}])"

            # Prefix + sign formatting for delta (keep 2 decimals)
            delta_num = pd.to_numeric(delta, errors="coerce")
            delta_txt = "N/A" if pd.isna(delta_num) else f"{float(delta_num):+.2f}"

            lines.append(
                f"- **{metric_name}:** Δ {delta_txt}{ci_txt} "
                f"(control {_fmt_num(control_mean)}; treatment {_fmt_num(treatment_mean)}; "
                f"n={n_control}/{n_treat})"
            )

        lines.append("")

    # remove trailing blank line if present
    while lines and lines[-1] == "":
        lines.pop()

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

    # v3 Section 4 Step 4: experiment results (optional; skip if spec missing)
    exp_lines = _render_experiments_md(week)
    if exp_lines:
        md.append("## Experiments")
        md.extend(exp_lines)
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

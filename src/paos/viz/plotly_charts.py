from __future__ import annotations

import pandas as pd
import plotly.express as px


def activity_trend(df: pd.DataFrame):
    d = df.sort_values("date").copy()
    fig = px.line(d, x="date", y="activity_level", markers=True, title="Activity Level Over Time")
    fig.update_layout(xaxis_title="Date", yaxis_title="Activity Level (0–100)")
    return fig


def status_counts(df: pd.DataFrame):
    counts = df["lifestyle_status"].value_counts().rename_axis("lifestyle_status").reset_index(name="count")
    fig = px.bar(counts, x="lifestyle_status", y="count", title="Lifestyle Status Counts")
    fig.update_layout(xaxis_title="Lifestyle Status", yaxis_title="Days")
    return fig


def activity_vs_energy(df: pd.DataFrame):
    d = df.copy()
    fig = px.scatter(
        d,
        x="activity_level",
        y="energy_focus",
        title="Activity Level vs Energy/Focus",
        hover_data=["date", "steps", "lifestyle_status"],
    )
    fig.update_layout(xaxis_title="Activity Level (0–100)", yaxis_title="Energy/Focus (1–5)")
    return fig

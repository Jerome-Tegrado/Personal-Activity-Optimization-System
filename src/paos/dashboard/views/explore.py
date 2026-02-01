from __future__ import annotations

import pandas as pd
import streamlit as st

from paos.dashboard.data import filter_by_date_range, hr_zone_breakdown
from paos.dashboard.ui import hero, section

STATUS_ORDER = ["Sedentary", "Lightly Active", "Active", "Very Active"]
PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}


@st.cache_data(show_spinner=False)
def _weekly_activity_trend(df: pd.DataFrame) -> pd.DataFrame:
    base = df.dropna(subset=["date", "activity_level"]).sort_values("date")
    return base.set_index("date")["activity_level"].resample("W").mean().reset_index()


@st.cache_data(show_spinner=False)
def _weekly_status_counts(df: pd.DataFrame) -> pd.DataFrame:
    base = df.dropna(subset=["date", "activity_level"]).sort_values("date")
    weekly = base.set_index("date")["activity_level"].resample("W").mean().reset_index()
    weekly["lifestyle_status"] = weekly["activity_level"].apply(_status_from_activity_level)
    counts = weekly["lifestyle_status"].value_counts().reset_index()
    counts.columns = ["lifestyle_status", "weeks"]
    return counts


@st.cache_data(show_spinner=False)
def _weekly_hr_zone(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    if metric not in {"days", "minutes"}:
        raise ValueError("metric must be 'days' or 'minutes'")

    base = df.dropna(subset=["date"]).copy()
    did = base["did_exercise"].astype(str).str.strip().str.lower()
    base = base[did == "yes"]

    base["heart_rate_zone"] = (
        base["heart_rate_zone"]
        .astype(str)
        .str.strip()
        .str.lower()
        .replace({"nan": "unknown", "none": "unknown", "": "unknown"})
    )

    base = base.set_index("date")

    if metric == "days":
        return base.groupby([pd.Grouper(freq="W"), "heart_rate_zone"]).size().reset_index(name="value")

    base["exercise_minutes"] = pd.to_numeric(base.get("exercise_minutes"), errors="coerce").fillna(0)
    return (
        base.groupby([pd.Grouper(freq="W"), "heart_rate_zone"])["exercise_minutes"]
        .sum()
        .reset_index(name="value")
    )


def _status_from_activity_level(level: float) -> str:
    if level <= 25:
        return "Sedentary"
    if level <= 50:
        return "Lightly Active"
    if level <= 75:
        return "Active"
    return "Very Active"


def render_explore(df: pd.DataFrame | None, filtered: pd.DataFrame | None) -> None:
    hero("Explore", "Fast charts with Apply-to-update controls.")

    if df is None or df.empty:
        st.info("Load an enriched CSV to explore charts.")
        return

    use = df.copy()
    if "date" in use.columns:
        use["date"] = pd.to_datetime(use["date"], errors="coerce")

    section("Controls", "Charts update only when you click Apply (reduces lag).")

    with st.form("explore_form", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            trend_granularity = st.selectbox("Trend granularity", ["Daily", "Weekly"], index=0)
        with c2:
            status_count_mode = st.selectbox("Status counts by", ["Days", "Weeks"], index=0)
        with c3:
            show_preview = st.toggle("Show data preview", value=False)

        start_ts = None
        end_ts = None
        if "date" in use.columns and use["date"].notna().any():
            min_date = use["date"].min().date()
            max_date = use["date"].max().date()
            start, end = st.date_input("Date range", value=(min_date, max_date))
            start_ts = pd.Timestamp(start) if start else None
            end_ts = pd.Timestamp(end) if end else None

        hr1, hr2 = st.columns(2)
        with hr1:
            hr_granularity = st.radio("HR granularity", ["Daily", "Weekly"], horizontal=True)
        with hr2:
            hr_metric_label = st.radio("HR measure", ["Exercise Days", "Exercise Minutes"], horizontal=True)

        apply = st.form_submit_button("Apply", type="primary", use_container_width=True)

    if apply:
        if start_ts is not None or end_ts is not None:
            use = filter_by_date_range(use, start=start_ts, end=end_ts, col="date")

    if use.empty:
        st.info("No rows after filters.")
        return

    section("Snapshot")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Days", len(use))
    with m2:
        st.metric("Avg Steps", f"{pd.to_numeric(use.get('steps'), errors='coerce').dropna().mean():.0f}" if "steps" in use.columns else "N/A")
    with m3:
        st.metric("Avg Activity", f"{pd.to_numeric(use.get('activity_level'), errors='coerce').dropna().mean():.1f}" if "activity_level" in use.columns else "N/A")
    with m4:
        st.metric("Avg Energy", f"{pd.to_numeric(use.get('energy_focus'), errors='coerce').dropna().mean():.2f}" if "energy_focus" in use.columns else "N/A")

    st.download_button(
        "Download filtered CSV",
        data=use.to_csv(index=False).encode("utf-8"),
        file_name="paos_filtered.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.divider()
    section("Charts")

    import plotly.express as px

    # Trend
    if "date" in use.columns and "activity_level" in use.columns:
        st.markdown("#### Activity Trend")
        chart_df = use.dropna(subset=["date"]).sort_values("date")
        if trend_granularity == "Weekly":
            weekly = _weekly_activity_trend(chart_df)
            fig = px.line(weekly, x="date", y="activity_level", markers=False)
        else:
            fig = px.line(chart_df, x="date", y="activity_level", markers=False)
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    # Scatter (WebGL)
    if {"activity_level", "energy_focus"}.issubset(use.columns):
        st.markdown("#### Activity vs Energy")
        scatter_df = use.dropna(subset=["activity_level", "energy_focus"]).copy()
        fig2 = px.scatter(
            scatter_df,
            x="activity_level",
            y="energy_focus",
            color="lifestyle_status" if "lifestyle_status" in scatter_df.columns else None,
            hover_data=["date"] if "date" in scatter_df.columns else None,
            render_mode="webgl",
        )
        fig2.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig2, use_container_width=True, config=PLOTLY_CONFIG)

    # Status counts
    if status_count_mode == "Weeks" and {"date", "activity_level"}.issubset(use.columns):
        st.markdown("#### Lifestyle Status (Weekly)")
        counts = _weekly_status_counts(use)
        fig3 = px.bar(counts, x="lifestyle_status", y="weeks", category_orders={"lifestyle_status": STATUS_ORDER})
        fig3.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig3, use_container_width=True, config=PLOTLY_CONFIG)
    elif "lifestyle_status" in use.columns:
        st.markdown("#### Lifestyle Status (Daily)")
        counts = use["lifestyle_status"].dropna().value_counts().reset_index()
        counts.columns = ["lifestyle_status", "days"]
        fig3 = px.bar(counts, x="lifestyle_status", y="days", category_orders={"lifestyle_status": STATUS_ORDER})
        fig3.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig3, use_container_width=True, config=PLOTLY_CONFIG)

    # HR zone
    st.markdown("#### Heart Rate Zones")
    hr_metric = "days" if hr_metric_label == "Exercise Days" else "minutes"
    if {"did_exercise", "heart_rate_zone"}.issubset(use.columns):
        if hr_granularity == "Daily":
            zone_df = hr_zone_breakdown(use, metric=hr_metric)
            figz = px.bar(zone_df, x="heart_rate_zone", y="value")
            figz.update_layout(margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(figz, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            if "date" in use.columns and use["date"].notna().any():
                weekly_zone = _weekly_hr_zone(use, metric=hr_metric)
                figz = px.bar(weekly_zone, x="date", y="value", color="heart_rate_zone", barmode="stack")
                figz.update_layout(margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(figz, use_container_width=True, config=PLOTLY_CONFIG)

    if show_preview:
        section("Preview")
        st.dataframe(use, width="stretch")

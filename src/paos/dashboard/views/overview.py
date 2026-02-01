from __future__ import annotations

import pandas as pd
import streamlit as st

import paos
from paos.dashboard.state import KEY_NAV
from paos.dashboard.ui import hero, section, tile


def _jump(target: str) -> None:
    st.session_state[KEY_NAV] = target
    st.rerun()


def render_overview(df: pd.DataFrame | None, filtered: pd.DataFrame | None) -> None:
    hero("Overview", "Your command center for activity + energy analytics.")

    if df is None or df.empty:
        st.info("Load an enriched CSV in the sidebar to begin.")
        return

    version = getattr(paos, "__version__", "unknown")
    date_info = "No valid dates"
    if "date" in df.columns:
        d = pd.to_datetime(df["date"], errors="coerce")
        if d.notna().any():
            date_info = f"{d.min().date()} → {d.max().date()}"

    st.caption(f"PAOS v{version} • Rows: {len(df)} • Date range: {date_info}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Days", len(df))
    with c2:
        st.metric("Avg Activity", f"{pd.to_numeric(df.get('activity_level'), errors='coerce').dropna().mean():.1f}" if "activity_level" in df.columns else "N/A")
    with c3:
        st.metric("Avg Steps", f"{pd.to_numeric(df.get('steps'), errors='coerce').dropna().mean():.0f}" if "steps" in df.columns else "N/A")
    with c4:
        st.metric("Avg Energy", f"{pd.to_numeric(df.get('energy_focus'), errors='coerce').dropna().mean():.2f}" if "energy_focus" in df.columns else "N/A")

    st.divider()

    section("Modules", "Everything stays in one dashboard shell. Pick a module.")
    r1 = st.columns(4)
    with r1[0]:
        tile("Explore", "Charts, trends, filters", "Charts")
        if st.button("Open Explore", use_container_width=True, type="primary"): _jump("Explore")
    with r1[1]:
        tile("Pipeline", "Run ingest / transform / report", "Run")
        if st.button("Open Pipeline", use_container_width=True): _jump("Pipeline")
    with r1[2]:
        tile("Reports", "Preview summary + exported charts", "View")
        if st.button("Open Reports", use_container_width=True): _jump("Reports")
    with r1[3]:
        tile("Benchmarks", "Compare your stats to cutpoints", "Compare")
        if st.button("Open Benchmarks", use_container_width=True): _jump("Benchmarks")

    r2 = st.columns(4)
    with r2[0]:
        tile("Experiments", "Control vs treatment effects", "Analyze")
        if st.button("Open Experiments", use_container_width=True): _jump("Experiments")
    with r2[1]:
        tile("Machine Learning", "Train + predict energy", "Model")
        if st.button("Open ML", use_container_width=True): _jump("Machine Learning")
    with r2[2]:
        tile("Settings", "Theme + preferences", "Shell")
        if st.button("Open Settings", use_container_width=True): _jump("Settings")
    with r2[3]:
        rec = None
        if "recommendation" in df.columns and df["recommendation"].notna().any():
            tmp = df.copy()
            if "date" in tmp.columns:
                tmp["date"] = pd.to_datetime(tmp["date"], errors="coerce")
                tmp = tmp.sort_values("date")
            rec = tmp["recommendation"].dropna().iloc[-1]
        tile("Latest Recommendation", rec or "No recommendation available yet.", "Now")
        st.button("OK", disabled=True, use_container_width=True)

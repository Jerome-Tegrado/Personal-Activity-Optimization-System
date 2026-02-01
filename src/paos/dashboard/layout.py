from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import streamlit as st

from paos.dashboard.data import DashboardDataConfig
from paos.dashboard.state import (
    KEY_DATA_SOURCE,
    KEY_ENRICHED_PATH,
    KEY_NAV,
    KEY_THEME,
    KEY_UPLOAD,
    DashboardPaths,
)

NavName = Literal[
    "Overview",
    "Explore",
    "Pipeline",
    "Reports",
    "Benchmarks",
    "Experiments",
    "Machine Learning",
    "Settings",
]

NAV: list[tuple[str, NavName]] = [
    ("Overview", "Overview"),
    ("Explore", "Explore"),
    ("Pipeline", "Pipeline"),
    ("Reports", "Reports"),
    ("Benchmarks", "Benchmarks"),
    ("Experiments", "Experiments"),
    ("Machine Learning", "Machine Learning"),
    ("Settings", "Settings"),
]


@dataclass(frozen=True)
class LayoutResult:
    nav: NavName
    data_source: str
    enriched_path: Path
    uploaded_bytes: bytes | None
    reset_clicked: bool
    clear_cache_clicked: bool
    theme_toggle_clicked: bool


def render_topbar() -> None:
    left, right = st.columns([3, 1], vertical_alignment="center")
    with left:
        st.markdown("## PAOS • Aurora Dashboard")
        st.caption("Fast modules • neon glass • single-home")
    with right:
        st.markdown('<span class="paos-chip">Shell</span>', unsafe_allow_html=True)


def render_sidebar(cfg: DashboardDataConfig, paths: DashboardPaths) -> LayoutResult:
    st.sidebar.markdown("### Navigation")
    current: NavName = st.session_state.get(KEY_NAV, "Overview")  # type: ignore[assignment]

    # Use compact buttons to feel more app-like
    for label, key in NAV:
        clicked = st.sidebar.button(
            label,
            key=f"nav_{key}",
            use_container_width=True,
            type="primary" if key == current else "secondary",
        )
        if clicked:
            st.session_state[KEY_NAV] = key
            st.rerun()

    st.sidebar.divider()

    # Utilities
    a, b = st.sidebar.columns(2)
    with a:
        reset_clicked = st.button("Reset", type="secondary", use_container_width=True)
    with b:
        clear_cache_clicked = st.button("Cache", type="secondary", use_container_width=True)

    st.sidebar.divider()

    # Theme toggle
    theme_toggle_clicked = False
    theme = st.session_state.get(KEY_THEME, "dark")
    is_light = theme == "light"
    new_is_light = st.sidebar.toggle("Light mode", value=is_light)
    if new_is_light != is_light:
        st.session_state[KEY_THEME] = "light" if new_is_light else "dark"
        theme_toggle_clicked = True

    st.sidebar.divider()

    # Data
    st.sidebar.markdown("### Data")
    data_source = st.sidebar.radio(
        "Data source",
        ["Processed file", "Upload CSV"],
        index=0,
        key=KEY_DATA_SOURCE,
    )

    uploaded_bytes: bytes | None = None
    enriched_path = Path(st.session_state.get(KEY_ENRICHED_PATH, str(paths.default_enriched_csv)))

    if data_source == "Processed file":
        csv_path_str = st.sidebar.text_input(
            "Enriched CSV path",
            value=str(enriched_path),
            key=KEY_ENRICHED_PATH,
        )
        enriched_path = Path(csv_path_str)
    else:
        up = st.sidebar.file_uploader(
            "Upload enriched CSV",
            type=["csv"],
            accept_multiple_files=False,
            key=KEY_UPLOAD,
        )
        if up is not None:
            uploaded_bytes = up.getvalue()

    with st.sidebar.expander("Expected columns", expanded=False):
        for col in (cfg.required_columns or []):
            st.write(f"- `{col}`")

    nav: NavName = st.session_state.get(KEY_NAV, "Overview")  # type: ignore[assignment]

    return LayoutResult(
        nav=nav,
        data_source=data_source,
        enriched_path=enriched_path,
        uploaded_bytes=uploaded_bytes,
        reset_clicked=reset_clicked,
        clear_cache_clicked=clear_cache_clicked,
        theme_toggle_clicked=theme_toggle_clicked,
    )

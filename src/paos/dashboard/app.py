from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from paos.dashboard.data import DashboardDataConfig, coerce_date_column, load_enriched_csv
from paos.dashboard.layout import render_sidebar, render_topbar
from paos.dashboard.scroll import inject_scroll_persistence
from paos.dashboard.state import DashboardPaths, init_state, reset_state
from paos.dashboard.theme import get_theme, inject_global_css, persist_theme
from paos.dashboard.views import VIEWS, render_unknown_view


@st.cache_data(show_spinner=False)
def _load_path_cached(path_str: str) -> pd.DataFrame:
    return load_enriched_csv(Path(path_str))


@st.cache_data(show_spinner=False)
def _load_upload_cached(file_bytes: bytes) -> pd.DataFrame:
    return load_enriched_csv(BytesIO(file_bytes))


def run_dashboard() -> None:
    st.set_page_config(page_title="PAOS Dashboard", layout="wide")

    paths = DashboardPaths()
    init_state(paths)

    theme = get_theme()
    inject_global_css(theme)

    # ✅ Fix the “scroll jumps to top” problem across Streamlit reruns
    inject_scroll_persistence()

    render_topbar()

    cfg = DashboardDataConfig()
    layout = render_sidebar(cfg, paths)

    # Theme toggle persistence (if your layout sets ui_theme in session_state)
    if getattr(layout, "theme_toggle_clicked", False):
        persist_theme(st.session_state.get("ui_theme", theme))
        st.rerun()

    if getattr(layout, "clear_cache_clicked", False):
        st.cache_data.clear()
        st.rerun()

    if getattr(layout, "reset_clicked", False):
        reset_state(paths)
        st.rerun()

    # Load data
    try:
        with st.spinner("Loading dataset…"):
            if layout.data_source == "Processed file":
                df = _load_path_cached(str(layout.enriched_path))
            else:
                if layout.uploaded_bytes is None:
                    st.info("Upload an enriched CSV to continue.")
                    st.stop()
                df = _load_upload_cached(layout.uploaded_bytes)

        if "date" in df.columns:
            df = coerce_date_column(df, col="date")

    except Exception as e:
        st.error("Failed to load data.")
        st.exception(e)
        st.stop()

    # Render selected view
    view_fn = VIEWS.get(layout.nav)
    if view_fn is None:
        render_unknown_view(layout.nav)
        return

    view_fn(df, None)

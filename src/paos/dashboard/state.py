from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import streamlit as st

KEY_NAV = "nav_section"

KEY_DATA_SOURCE = "data_source"
KEY_ENRICHED_PATH = "data_enriched_path"
KEY_UPLOAD = "data_upload"

KEY_THEME = "ui_theme"  # "dark" | "light"


@dataclass(frozen=True)
class DashboardPaths:
    default_enriched_csv: Path = Path("data/processed/daily_log_enriched.csv")


def init_state(paths: DashboardPaths) -> None:
    st.session_state.setdefault(KEY_NAV, "Overview")
    st.session_state.setdefault(KEY_DATA_SOURCE, "Processed file")
    st.session_state.setdefault(KEY_ENRICHED_PATH, str(paths.default_enriched_csv))
    st.session_state.setdefault(KEY_THEME, "dark")


def reset_state(paths: DashboardPaths) -> None:
    theme = st.session_state.get(KEY_THEME, "dark")
    st.session_state.clear()
    st.session_state[KEY_THEME] = theme

    st.session_state[KEY_NAV] = "Overview"
    st.session_state[KEY_DATA_SOURCE] = "Processed file"
    st.session_state[KEY_ENRICHED_PATH] = str(paths.default_enriched_csv)
    st.session_state.pop(KEY_UPLOAD, None)

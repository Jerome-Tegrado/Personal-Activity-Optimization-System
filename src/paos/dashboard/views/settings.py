from __future__ import annotations

import streamlit as st

from paos.dashboard.ui import hero, section, tile


def render_settings(df, filtered) -> None:
    hero("Settings", "Shell preferences and dashboard behavior.")

    section("Notes")
    tile(
        "Theme behavior",
        "Light/Dark is persisted via query params (?theme=light|dark). "
        "This avoids forced reload tricks that can cause lag.",
        "Theme",
    )
    tile(
        "Performance tips",
        "Explore charts update only on Apply. Scatter uses WebGL for speed. "
        "Plotly modebar hidden for smoother rendering.",
        "Speed",
    )

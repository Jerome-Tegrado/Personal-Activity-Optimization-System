from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from paos.dashboard.ui import hero, section


def _render_html(path: Path) -> None:
    html = path.read_text(encoding="utf-8", errors="ignore")
    components.html(html, height=680, scrolling=True)


def render_reports(df, filtered) -> None:
    hero("Reports", "Preview summaries and charts inside the dashboard.")

    out_dir = Path(st.text_input("Reports directory", value="reports"))

    summary = out_dir / "summary.md"
    interactive_dir = out_dir / "figures" / "interactive"
    static_dir = out_dir / "figures" / "static"

    if not out_dir.exists():
        st.info("No reports folder found yet. Use **Pipeline → all/report** to generate outputs.")
        return

    tabs = st.tabs(["Summary", "Interactive", "Static"])

    with tabs[0]:
        section("Summary")
        if summary.exists():
            st.markdown(summary.read_text(encoding="utf-8", errors="ignore"))
        else:
            st.info("No summary.md found. Generate it via Pipeline.")

    with tabs[1]:
        section("Interactive charts")
        if interactive_dir.exists():
            files = sorted(interactive_dir.glob("*.html"))
            if not files:
                st.info("No interactive HTML charts found.")
            else:
                pick = st.selectbox("Choose a chart", options=[f.name for f in files])
                _render_html(interactive_dir / pick)
        else:
            st.info("No interactive charts folder found.")

    with tabs[2]:
        section("Static charts")
        if static_dir.exists():
            imgs = sorted(static_dir.glob("*.png"))
            if not imgs:
                st.info("No PNG charts found.")
            else:
                pick = st.selectbox("Choose an image", options=[p.name for p in imgs])
                st.image(str(static_dir / pick), use_container_width=True)
        else:
            st.info("No static charts folder found.")

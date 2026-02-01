from __future__ import annotations

import streamlit as st


def chip(text: str) -> None:
    st.markdown(f'<span class="paos-chip">{text}</span>', unsafe_allow_html=True)


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
<div style="display:flex; justify-content:space-between; align-items:flex-end; gap:16px;">
  <div>
    <div class="paos-title" style="font-size: 1.7rem; font-weight: 800;">{title}</div>
    <div class="paos-muted" style="margin-top:4px;">{subtitle}</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def card(title: str, subtitle: str | None = None, right: str | None = None) -> None:
    subtitle_html = f'<div class="paos-muted" style="margin-top:6px;">{subtitle}</div>' if subtitle else ""
    right_html = f'<span class="paos-chip">{right}</span>' if right else ""
    st.markdown(
        f"""
<div class="paos-card">
  <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
    <div style="font-weight:800; font-size:1.05rem;">{title}</div>
    {right_html}
  </div>
  {subtitle_html}
</div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, hint: str | None = None) -> None:
    st.markdown(f"### {title}")
    if hint:
        st.caption(hint)


def tile(title: str, desc: str, tag: str | None = None) -> None:
    tag_html = f'<span class="paos-chip">{tag}</span>' if tag else ""
    st.markdown(
        f"""
<div class="paos-card">
  <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
    <div style="font-weight:850;">{title}</div>
    {tag_html}
  </div>
  <div class="paos-muted" style="margin-top:6px;">{desc}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

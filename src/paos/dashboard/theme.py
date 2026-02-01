from __future__ import annotations

import streamlit as st

from paos.dashboard.state import KEY_THEME

THEME_PARAM = "theme"


def _normalize_theme(v: str | None) -> str:
    v = (v or "").strip().lower()
    return "light" if v == "light" else "dark"


def get_theme() -> str:
    qp = st.query_params.get(THEME_PARAM)
    if qp is not None:
        t = _normalize_theme(qp)
        st.session_state[KEY_THEME] = t
        return t
    return _normalize_theme(st.session_state.get(KEY_THEME, "dark"))


def persist_theme(theme: str) -> None:
    t = _normalize_theme(theme)
    st.session_state[KEY_THEME] = t
    st.query_params[THEME_PARAM] = t


def inject_global_css(theme: str) -> None:
    t = _normalize_theme(theme)

    if t == "dark":
        tokens = {
            "bg": "#05070B",
            "panel": "rgba(10, 14, 18, 0.86)",
            "card": "rgba(14, 18, 26, 0.78)",
            "text": "#EAF2FF",
            "muted": "#9AA7C0",
            "border": "rgba(255,255,255,0.10)",
            "a": "#22C55E",  # green
            "b": "#38BDF8",  # blue
            "shadow": "0 18px 55px rgba(0,0,0,0.62)",
            "scroll_track": "rgba(255,255,255,0.06)",
            "scroll_thumb": "rgba(56,189,248,0.35)",
            "scroll_thumb_hover": "rgba(34,197,94,0.55)",
        }
    else:
        tokens = {
            "bg": "#F6F7FB",
            "panel": "rgba(255,255,255,0.94)",
            "card": "#FFFFFF",
            "text": "#0B1220",
            "muted": "#475569",
            "border": "rgba(11,18,32,0.12)",
            "a": "#16A34A",
            "b": "#0284C7",
            "shadow": "0 12px 40px rgba(11,18,32,0.10)",
            "scroll_track": "rgba(11,18,32,0.08)",
            "scroll_thumb": "rgba(2,132,199,0.35)",
            "scroll_thumb_hover": "rgba(22,163,74,0.45)",
        }

    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {{
  --bg: {tokens["bg"]};
  --panel: {tokens["panel"]};
  --card: {tokens["card"]};
  --text: {tokens["text"]};
  --muted: {tokens["muted"]};
  --border: {tokens["border"]};
  --a: {tokens["a"]};
  --b: {tokens["b"]};
  --shadow: {tokens["shadow"]};
  --radius: 14px;

  --scroll-track: {tokens["scroll_track"]};
  --scroll-thumb: {tokens["scroll_thumb"]};
  --scroll-thumb-hover: {tokens["scroll_thumb_hover"]};
}}

@keyframes pageIn {{
  from {{ opacity: 0; transform: translateY(6px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes scan {{
  0% {{ opacity: .10; transform: translateY(-40px); }}
  100% {{ opacity: .10; transform: translateY(60vh); }}
}}

/* ✅ FIX: remove Streamlit header/toolbar that overlaps content */
header[data-testid="stHeader"] {{
  display: none !important;
}}
div[data-testid="stToolbar"] {{
  display: none !important;
}}

/* ✅ smoother scrolling feel */
html {{
  scroll-behavior: smooth;
}}
/* prevent layout shift + nicer scrolling */
body {{
  overscroll-behavior-y: none;
}}

/* ✅ Custom scrollbar (main) */
::-webkit-scrollbar {{
  width: 12px;
  height: 12px;
}}
::-webkit-scrollbar-track {{
  background: var(--scroll-track);
  border-radius: 999px;
}}
::-webkit-scrollbar-thumb {{
  background: var(--scroll-thumb);
  border-radius: 999px;
  border: 2px solid rgba(0,0,0,0);
  background-clip: padding-box;
}}
::-webkit-scrollbar-thumb:hover {{
  background: var(--scroll-thumb-hover);
}}
/* Firefox */
* {{
  scrollbar-width: thin;
  scrollbar-color: var(--scroll-thumb) var(--scroll-track);
}}

.stApp {{
  background:
    linear-gradient(transparent 31px, rgba(255,255,255,0.03) 32px),
    linear-gradient(90deg, transparent 31px, rgba(255,255,255,0.03) 32px),
    radial-gradient(900px 600px at 12% 10%, color-mix(in srgb, var(--b) 14%, transparent), transparent 60%),
    radial-gradient(900px 600px at 88% 0%, color-mix(in srgb, var(--a) 14%, transparent), transparent 62%),
    var(--bg);
  background-size: 32px 32px, 32px 32px, auto, auto, auto;
  color: var(--text);
}}

.block-container {{
  padding-top: 1.85rem !important;
  padding-bottom: 2rem;
  max-width: 1240px;
  animation: pageIn .20s ease-out both;
}}

section[data-testid="stSidebar"] {{
  background: var(--panel) !important;
  border-right: 1px solid var(--border);
  backdrop-filter: blur(12px);
}}

#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}

/* HARD APPLY FONT */
.stApp, .stApp * {{
  font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace !important;
}}
[data-testid="stMarkdownContainer"] * {{
  font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace !important;
}}
label, input, textarea, button {{
  font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace !important;
}}

.paos-card {{
  position: relative;
  background: var(--card);
  border: 1px solid color-mix(in srgb, var(--border) 70%, var(--b));
  border-radius: var(--radius);
  padding: 16px 16px;
  box-shadow: var(--shadow);
  transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
}}
.paos-card:hover {{
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--a) 50%, var(--border));
  box-shadow: 0 24px 80px rgba(0,0,0,0.55);
}}
.paos-card::after {{
  content: "";
  position: absolute;
  left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--b), transparent);
  animation: scan 4.2s linear infinite;
}}

.paos-muted {{ color: var(--muted); }}

.paos-chip {{
  display:inline-flex;
  align-items:center;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: rgba(255,255,255,0.04);
  color: var(--muted);
  font-size: 12px;
}}

div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
textarea {{
  border-radius: 12px !important;
  border: 1px solid color-mix(in srgb, var(--border) 70%, var(--b)) !important;
  background: color-mix(in srgb, var(--card) 92%, transparent) !important;
}}

button {{
  border-radius: 12px !important;
  transition: transform .10s ease, filter .10s ease !important;
}}
button:hover {{
  transform: translateY(-1px);
  filter: brightness(1.02);
}}
button[kind="primary"] {{
  background: linear-gradient(90deg, var(--a), var(--b)) !important;
  border: 0 !important;
}}
button[kind="secondary"] {{
  border: 1px solid var(--border) !important;
  background: rgba(255,255,255,0.03) !important;
}}

@media (prefers-reduced-motion: reduce) {{
  .paos-card::after {{ animation: none !important; }}
  .block-container {{ animation: none !important; }}
  button {{ transition: none !important; }}
  .paos-card {{ transition: none !important; }}
}}
</style>
        """,
        unsafe_allow_html=True,
    )

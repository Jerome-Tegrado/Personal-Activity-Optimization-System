from __future__ import annotations

import streamlit.components.v1 as components


def inject_scroll_persistence() -> None:
    """
    Persist the main page scroll position across Streamlit reruns.

    Streamlit reruns rebuild the DOM and the browser may jump to top.
    This snippet stores window.parent.scrollY and restores it after rerender.
    Guarded so event listeners are registered only once.
    """
    components.html(
        """
<script>
(() => {
  const KEY = "paos_scroll_y_v2";
  const P = window.parent;

  // Guard: avoid attaching multiple listeners across reruns
  try {
    if (P.__PAOS_SCROLL_INIT__) return;
    P.__PAOS_SCROLL_INIT__ = true;
  } catch (e) {
    // If we can't access parent, silently do nothing
    return;
  }

  function getY() {
    try {
      return P.scrollY || P.document.documentElement.scrollTop || 0;
    } catch (e) { return 0; }
  }

  function setY(y) {
    try { P.scrollTo(0, y); } catch (e) {}
  }

  // Save current scroll position (passive for performance)
  try {
    P.addEventListener("scroll", () => {
      sessionStorage.setItem(KEY, String(getY()));
      sessionStorage.setItem(KEY + "_ts", String(Date.now()));
    }, { passive: true });
  } catch (e) {}

  // Restore after render: repeat a few times to handle delayed layout/charts
  function restore() {
    const yRaw = sessionStorage.getItem(KEY);
    if (!yRaw) return;

    const y = parseInt(yRaw, 10);
    if (!Number.isFinite(y)) return;

    // If user last scrolled a long time ago, don't force restore
    const tsRaw = sessionStorage.getItem(KEY + "_ts");
    const ts = tsRaw ? parseInt(tsRaw, 10) : 0;
    if (ts && (Date.now() - ts) > 1000 * 60 * 30) return; // 30 min

    // Restore multiple times (charts/widgets can shift layout)
    let tries = 0;
    const maxTries = 10;

    const tick = () => {
      tries += 1;
      setY(y);
      if (tries < maxTries) {
        requestAnimationFrame(() => setTimeout(tick, 80));
      }
    };

    // Start shortly after load
    setTimeout(tick, 50);
  }

  // Hook into iframe load (best effort)
  try {
    window.addEventListener("load", restore);
  } catch (e) {}

  // Also restore immediately (covers some Streamlit render paths)
  restore();
})();
</script>
        """,
        height=0,
    )

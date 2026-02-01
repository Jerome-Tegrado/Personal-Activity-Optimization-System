from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from paos.dashboard.ui import hero, section


def render_benchmarks(df: pd.DataFrame | None, filtered: pd.DataFrame | None) -> None:
    hero("Benchmarks", "Compare your metrics to cutpoints.")

    if df is None or df.empty:
        st.info("Load an enriched CSV first.")
        return

    section("Setup", "Uses Apply to avoid slow reruns.")
    with st.form("bench_form", clear_on_submit=False):
        spec_path = Path(st.text_input("Benchmarks spec CSV", value="data/sample/benchmarks.csv"))
        group = st.text_input("Group", value="adult")
        metrics = st.multiselect(
            "Metrics",
            options=sorted(list(df.columns)),
            default=[c for c in ["steps", "activity_level"] if c in df.columns],
        )
        run = st.form_submit_button("Apply", type="primary", use_container_width=True)

    if not run:
        st.info("Click Apply to compute benchmark comparisons.")
        return

    if not spec_path.exists():
        st.warning(f"Benchmarks spec not found: {spec_path}")
        return

    # Lazy import to keep initial load fast
    from paos.benchmarks.compare import compare_to_benchmarks

    results = compare_to_benchmarks(df, spec_path, group=group, metrics=tuple(metrics))

    if not results:
        st.info("No benchmark results (spec missing metrics or data empty).")
        return

    rows = []
    for r in results:
        rows.append(
            {
                "metric": r.metric,
                "group": r.group,
                "unit": r.unit,
                "user_mean": r.user_mean,
                "user_median": r.user_median,
                "approx_percentile": r.approx_percentile,
                "p25": r.benchmark_p25,
                "p50": r.benchmark_p50,
                "p75": r.benchmark_p75,
                "p90": r.benchmark_p90,
                "source": r.source,
            }
        )

    section("Results")
    st.dataframe(pd.DataFrame(rows), width="stretch")

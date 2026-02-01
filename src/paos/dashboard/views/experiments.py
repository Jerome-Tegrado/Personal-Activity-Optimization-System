from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from paos.dashboard.ui import hero, section


def render_experiments(df: pd.DataFrame | None, filtered: pd.DataFrame | None) -> None:
    hero("Experiments", "Compute control vs treatment effects from an experiment spec.")

    if df is None or df.empty:
        st.info("Load an enriched CSV first.")
        return

    section("Setup", "Uses Apply to avoid reruns while choosing options.")
    with st.form("exp_form", clear_on_submit=False):
        spec_path = Path(st.text_input("Experiments spec CSV", value="data/sample/experiments.csv"))
        metric_choices = [c for c in ("activity_level", "energy_focus", "steps") if c in df.columns]
        metrics = st.multiselect("Metrics", options=sorted(df.columns), default=metric_choices or [])

        add_ci = st.toggle("Bootstrap CI", value=True)
        n_boot = st.number_input("n_boot", min_value=0, max_value=10000, value=2000, step=100)
        ci = st.slider("CI", min_value=0.50, max_value=0.99, value=0.95, step=0.01)

        run = st.form_submit_button("Apply", type="primary", use_container_width=True)

    if not run:
        st.info("Click Apply to compute effects.")
        return

    if not spec_path.exists():
        st.warning("Experiments spec not found. Provide a valid spec CSV path.")
        return

    if not metrics:
        st.info("Select at least one metric.")
        return

    # Lazy import
    from paos.experiments.assign import assign_experiments_to_days
    from paos.experiments.effects import compute_experiment_effects

    try:
        assigned = assign_experiments_to_days(df, spec_path, date_col="date")
        effects = compute_experiment_effects(
            assigned,
            experiment_col="experiment",
            phase_col="experiment_phase",
            metrics=tuple(metrics),
            add_ci=bool(add_ci),
            n_boot=int(n_boot),
            ci=float(ci),
        )
        section("Effects")
        st.dataframe(effects, width="stretch")
    except Exception as e:
        st.exception(e)

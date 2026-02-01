from __future__ import annotations

from pathlib import Path

import streamlit as st

from paos.dashboard.ui import hero, section


def render_machine_learning(df, filtered) -> None:
    hero("Machine Learning", "Train/evaluate and write predictions into a new CSV.")

    section("Actions", "Uses buttons so nothing runs until requested.")

    enriched_csv = Path(st.text_input("Enriched CSV path", value="data/processed/daily_log_enriched.csv"))
    model_path = Path(st.text_input("Model path", value="models/energy_model.pkl"))
    eval_out = Path(st.text_input("Eval JSON output", value="reports/model/energy_eval.json"))
    pred_out = Path(st.text_input("Predictions CSV output", value="data/processed/daily_log_enriched_with_preds.csv"))

    model_type = st.selectbox("Model type", ["ridge", "rf"], index=0)
    test_size = st.slider("Test size", min_value=0.1, max_value=0.5, value=0.2, step=0.05)

    c1, c2 = st.columns(2)
    do_train = c1.button("Train + Evaluate", type="primary", use_container_width=True)
    do_pred = c2.button("Predict into CSV", type="secondary", use_container_width=True)

    if do_train:
        try:
            from paos.machine_learning.cli import train_and_evaluate_from_enriched_csv

            if not enriched_csv.exists():
                raise FileNotFoundError(f"Missing enriched CSV: {enriched_csv}")

            model_path.parent.mkdir(parents=True, exist_ok=True)
            eval_out.parent.mkdir(parents=True, exist_ok=True)

            out = train_and_evaluate_from_enriched_csv(
                enriched_csv_path=enriched_csv,
                model_out_path=model_path,
                eval_out_path=eval_out,
                model_type=model_type,
                test_size=float(test_size),
            )
            st.success(f"Saved model → {model_path}")
            st.success(f"Saved eval → {eval_out}")
            st.json(out)
        except Exception as e:
            st.exception(e)

    if do_pred:
        try:
            from paos.machine_learning.cli import predict_energy_into_csv

            if not enriched_csv.exists():
                raise FileNotFoundError(f"Missing enriched CSV: {enriched_csv}")
            if not model_path.exists():
                raise FileNotFoundError(f"Missing model: {model_path}")

            pred_out.parent.mkdir(parents=True, exist_ok=True)
            predict_energy_into_csv(enriched_csv_path=enriched_csv, model_path=model_path, out_csv_path=pred_out)
            st.success(f"Wrote predictions → {pred_out}")
        except Exception as e:
            st.exception(e)

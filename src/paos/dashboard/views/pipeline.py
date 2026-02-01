from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from paos.dashboard.ui import hero, section


def render_pipeline(df: pd.DataFrame | None, filtered: pd.DataFrame | None) -> None:
    hero("Pipeline", "Run ingest → transform → report without leaving the dashboard.")

    section("Run", "Uses a form so nothing runs until you click Execute.")

    with st.form("pipeline_form", clear_on_submit=False):
        stage = st.selectbox("Stage", ["ingest", "transform", "report", "all"], index=3)
        input_type = st.selectbox("Input type", ["csv", "sheets"], index=0)

        col1, col2 = st.columns(2)
        with col1:
            processed_path = st.text_input(
                "Processed/enriched CSV output",
                value="data/processed/daily_log_enriched.csv",
            )
        with col2:
            out_dir = st.text_input("Reports output dir", value="reports")

        no_figures = st.toggle("Skip figures (--no-figures)", value=False)

        st.markdown("#### Input options")
        if input_type == "csv":
            csv_path = st.text_input("Input CSV path", value="data/sample/daily_log.csv")
            sheets_id = None
            sheets_range = None
            dump_raw = False
            raw_out = "data/processed/sheets_raw.csv"
        else:
            csv_path = None
            sheets_id = st.text_input("Sheets ID (spreadsheet_id)", value="")
            sheets_range = st.text_input("Sheets range (A1)", value="Form Responses 1!A1:J")
            dump_raw = st.toggle("Dump raw Sheets snapshot", value=False)
            raw_out = st.text_input("Raw snapshot output", value="data/processed/sheets_raw.csv")

        run = st.form_submit_button("Execute", type="primary", use_container_width=True)

    if not run:
        st.info("Configure the pipeline, then click **Execute**.")
        return

    # Lazy imports (reduce initial load / lag)
    from paos.analysis.summary import write_weekly_summary
    from paos.ingest import load_daily_log
    from paos.transform.scoring import enrich
    from paos.viz.export import export_figures

    processed = Path(processed_path)
    processed.parent.mkdir(parents=True, exist_ok=True)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    with st.status("Running…", expanded=True) as status:
        try:
            df_raw: pd.DataFrame | None = None
            if stage in {"ingest", "transform", "all"}:
                status.update(label="Ingesting data…", state="running")
                if input_type == "csv":
                    if not csv_path:
                        raise ValueError("CSV input path is required.")
                    df_raw = load_daily_log("csv", path=csv_path)
                else:
                    if not sheets_id or not sheets_range:
                        raise ValueError("Sheets ID and range are required.")
                    df_raw = load_daily_log(
                        "sheets",
                        spreadsheet_id=sheets_id,
                        range_=sheets_range,
                        dump_raw_path=raw_out if dump_raw else None,
                    )
                st.write(f"Ingested rows: {len(df_raw)}")

            df_enriched: pd.DataFrame | None = None
            if stage in {"transform", "all"}:
                status.update(label="Transforming (scoring/enrich)…", state="running")
                if df_raw is None:
                    raise ValueError("Transform requires ingest output.")
                df_enriched = enrich(df_raw)
                df_enriched.to_csv(processed, index=False)
                st.success(f"Wrote enriched CSV → {processed}")

            elif stage == "ingest":
                if df_raw is not None:
                    df_raw.to_csv(processed, index=False)
                    st.success(f"Wrote ingested CSV snapshot → {processed}")

            if stage in {"report", "all"}:
                status.update(label="Building report…", state="running")
                if stage == "report":
                    if not processed.exists():
                        raise FileNotFoundError(f"Processed CSV not found: {processed}")
                    df_enriched = pd.read_csv(processed)

                if df_enriched is None:
                    raise ValueError("Report requires enriched data.")

                summary_path = out / "summary.md"
                write_weekly_summary(df_enriched, summary_path)

                if not no_figures:
                    export_figures(df_enriched, out)

                st.success(f"Report complete → {out}")
                st.write(f"Summary: {summary_path}")

            status.update(label="Done ✅", state="complete")
        except Exception as e:
            status.update(label="Failed ❌", state="error")
            st.exception(e)

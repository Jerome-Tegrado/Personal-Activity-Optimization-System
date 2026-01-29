from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from paos.dashboard.data import (
    DashboardDataConfig,
    coerce_date_column,
    filter_by_date_range,
    load_enriched_csv,
    validate_required_columns,
)

DEFAULT_ENRICHED_CSV = Path("data/processed/daily_log_enriched.csv")


@st.cache_data
def _load_cached(path_str: str) -> pd.DataFrame:
    # cache_data prefers hashable inputs; strings are safest
    return load_enriched_csv(Path(path_str))


def main() -> None:
    st.set_page_config(page_title="PAOS Dashboard", layout="wide")
    st.title("PAOS Dashboard (v2)")

    st.write(
        "This dashboard loads the **enriched PAOS CSV** and helps you explore activity + energy trends."
    )

    st.sidebar.header("Options")
    show_checks = st.sidebar.checkbox("Show data checks", value=True)
    show_preview = st.sidebar.checkbox("Show data preview", value=False)

    cfg = DashboardDataConfig()

    csv_path_str = st.text_input("Enriched CSV path", value=str(DEFAULT_ENRICHED_CSV))
    csv_path = Path(csv_path_str)

    try:
        df = _load_cached(str(csv_path))
    except FileNotFoundError:
        st.error(
            f"Could not find the enriched CSV at: `{csv_path}`\n\n"
            "Run:\n"
            "`python scripts/paos_run.py transform --input-type csv --input data/sample/daily_log.csv "
            "--processed data/processed/daily_log_enriched.csv`"
        )
        st.stop()

    # -----------------------
    # Parse date (safe)
    # -----------------------
    if "date" in df.columns:
        df = coerce_date_column(df, col="date")

    # -----------------------
    # Data checks (friendly)
    # -----------------------
    if show_checks:
        st.subheader("Data checks")

        try:
            validate_required_columns(df, cfg.required_columns)
            st.success("Looks good — expected columns found.")
        except ValueError as e:
            msg = str(e)
            st.warning(msg)

            missing = [c for c in cfg.required_columns if c not in df.columns]
            if missing:
                st.warning(
                    "Some expected columns are missing:\n\n"
                    + "\n".join([f"- `{c}`" for c in missing])
                )

            st.info(
                "This can happen if you loaded a non-enriched CSV. "
                "Try generating the enriched file using the transform stage."
            )

        if "date" in df.columns:
            if df["date"].isna().all() and len(df) > 0:
                st.warning(
                    "The `date` column exists, but none of the values could be parsed as valid dates."
                )

    # -----------------------
    # Quick metrics
    # -----------------------
    st.subheader("Quick metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Days logged", len(df))

    with col2:
        if "activity_level" in df.columns and len(df) > 0:
            st.metric("Avg Activity Level", f"{df['activity_level'].mean():.1f}")
        else:
            st.metric("Avg Activity Level", "N/A")

    with col3:
        if "energy_focus" in df.columns and len(df) > 0:
            st.metric("Avg Energy/Focus", f"{df['energy_focus'].mean():.2f}")
        else:
            st.metric("Avg Energy/Focus", "N/A")

    # -----------------------
    # Filter
    # -----------------------
    st.subheader("Filter")

    filtered = df.copy()

    if "date" in filtered.columns and filtered["date"].notna().any():
        min_date = filtered["date"].min().date()
        max_date = filtered["date"].max().date()

        start, end = st.date_input("Date range", value=(min_date, max_date))

        start_ts = pd.Timestamp(start) if start else None
        end_ts = pd.Timestamp(end) if end else None
        filtered = filter_by_date_range(filtered, start=start_ts, end=end_ts, col="date")

    if filtered.empty:
        st.info("No rows to show (empty dataset or date range filter returned 0 rows).")

    st.download_button(
        label="Download filtered CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="paos_filtered.csv",
        mime="text/csv",
        disabled=filtered.empty,
    )

    # -----------------------
    # Summary stats (filtered)
    # -----------------------
    st.subheader("Summary stats (filtered)")

    if len(filtered) > 0:
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric("Days", len(filtered))

        with c2:
            if "steps" in filtered.columns:
                st.metric("Avg Steps", f"{filtered['steps'].mean():.0f}")
            else:
                st.metric("Avg Steps", "N/A")

        with c3:
            if "activity_level" in filtered.columns:
                st.metric("Avg Activity", f"{filtered['activity_level'].mean():.1f}")
            else:
                st.metric("Avg Activity", "N/A")

        with c4:
            if "energy_focus" in filtered.columns:
                st.metric("Avg Energy", f"{filtered['energy_focus'].mean():.2f}")
            else:
                st.metric("Avg Energy", "N/A")
    else:
        st.info("No summary stats available for an empty filter.")

    # -----------------------
    # Activity trend (chart)
    # -----------------------
    st.subheader("Activity trend")

    if (
        "date" in filtered.columns
        and "activity_level" in filtered.columns
        and filtered["date"].notna().any()
        and len(filtered) > 0
    ):
        chart_df = filtered.dropna(subset=["date"]).sort_values("date")
        fig = px.line(chart_df, x="date", y="activity_level", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Trend chart needs valid `date` and `activity_level` data.")

    # -----------------------
    # Activity vs Energy (scatter)
    # -----------------------
    st.subheader("Activity vs Energy/Focus")

    if (
        "activity_level" in filtered.columns
        and "energy_focus" in filtered.columns
        and len(filtered) > 0
    ):
        scatter_df = filtered.dropna(subset=["activity_level", "energy_focus"]).copy()
        hover_cols = ["activity_level", "energy_focus"]

        if "date" in scatter_df.columns:
            hover_cols = ["date"] + hover_cols

        color_col = (
            "lifestyle_status" if "lifestyle_status" in scatter_df.columns else None
        )

        fig2 = px.scatter(
            scatter_df,
            x="activity_level",
            y="energy_focus",
            hover_data=hover_cols,
            color=color_col,
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Scatter plot needs `activity_level` and `energy_focus` data.")

    # -----------------------
    # Lifestyle status counts
    # -----------------------
    st.subheader("Lifestyle status counts")

    if "lifestyle_status" in filtered.columns and len(filtered) > 0:
        counts = filtered["lifestyle_status"].dropna().value_counts().reset_index()
        counts.columns = ["lifestyle_status", "days"]

        fig3 = px.bar(counts, x="lifestyle_status", y="days")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Status chart needs `lifestyle_status` data.")

    # -----------------------
    # Preview
    # -----------------------
    if show_preview:
        st.subheader("Data preview")
        st.dataframe(filtered, width="stretch")


if __name__ == "__main__":
    main()

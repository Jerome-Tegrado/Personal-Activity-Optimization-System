from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from paos.dashboard.data import (
    DashboardDataConfig,
    coerce_date_column,
    filter_by_date_range,
    hr_zone_breakdown,
    load_enriched_csv,
    validate_required_columns,
)

DEFAULT_ENRICHED_CSV = Path("data/processed/daily_log_enriched.csv")
STATUS_ORDER = ["Sedentary", "Lightly Active", "Active", "Very Active"]

# Widget keys (centralized so reset is easy + consistent)
KEY_SHOW_CHECKS = "opt_show_checks"
KEY_SHOW_PREVIEW = "opt_show_preview"
KEY_TREND_GRANULARITY = "opt_trend_granularity"
KEY_STATUS_COUNT_MODE = "opt_status_count_mode"

KEY_DATA_SOURCE = "data_source"
KEY_ENRICHED_PATH = "data_enriched_path"
KEY_UPLOAD = "data_upload"

KEY_DATE_RANGE = "filter_date_range"
KEY_HR_GRANULARITY = "hr_zone_granularity"
KEY_HR_METRIC = "hr_zone_metric"


@st.cache_data
def _load_cached(path_str: str) -> pd.DataFrame:
    # cache_data prefers hashable inputs; strings are safest
    return load_enriched_csv(Path(path_str))


@st.cache_data
def _load_uploaded_cached(file_bytes: bytes) -> pd.DataFrame:
    # cache_data prefers hashable inputs; bytes are hashable
    from io import BytesIO

    return load_enriched_csv(BytesIO(file_bytes))


@st.cache_data
def _filter_cached(
    df: pd.DataFrame, start: pd.Timestamp | None, end: pd.Timestamp | None
) -> pd.DataFrame:
    # Cached wrapper around the existing helper.
    # Note: df is hashable for Streamlit cache, but can be large; this is still a net win
    # for typical dashboard usage. If it ever becomes too heavy, we can cache on a smaller
    # signature later (e.g., df hash + dates).
    return filter_by_date_range(df, start=start, end=end, col="date")


@st.cache_data
def _weekly_activity_trend(df: pd.DataFrame) -> pd.DataFrame:
    base = df.dropna(subset=["date", "activity_level"]).sort_values("date")
    return (
        base.set_index("date")["activity_level"]
        .resample("W")
        .mean()
        .reset_index()
    )


@st.cache_data
def _weekly_status_counts(df: pd.DataFrame) -> pd.DataFrame:
    base = df.dropna(subset=["date", "activity_level"]).sort_values("date")
    weekly = (
        base.set_index("date")["activity_level"]
        .resample("W")
        .mean()
        .reset_index()
    )
    weekly["lifestyle_status"] = weekly["activity_level"].apply(_status_from_activity_level)
    counts = weekly["lifestyle_status"].value_counts().reset_index()
    counts.columns = ["lifestyle_status", "weeks"]
    return counts


@st.cache_data
def _weekly_hr_zone(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    # Produces weekly HR zone breakdown for exercised rows.
    # metric: "days" or "minutes"
    if metric not in {"days", "minutes"}:
        raise ValueError("metric must be 'days' or 'minutes'")

    base = df.dropna(subset=["date"]).copy()

    did = base["did_exercise"].astype(str).str.strip().str.lower()
    base = base[did == "yes"]

    base["heart_rate_zone"] = (
        base["heart_rate_zone"]
        .astype(str)
        .str.strip()
        .str.lower()
        .replace({"nan": "unknown", "none": "unknown", "": "unknown"})
    )

    base = base.set_index("date")

    if metric == "days":
        weekly_zone = (
            base.groupby([pd.Grouper(freq="W"), "heart_rate_zone"])
            .size()
            .reset_index(name="value")
        )
    else:
        base["exercise_minutes"] = pd.to_numeric(
            base.get("exercise_minutes"), errors="coerce"
        ).fillna(0)
        weekly_zone = (
            base.groupby([pd.Grouper(freq="W"), "heart_rate_zone"])["exercise_minutes"]
            .sum()
            .reset_index(name="value")
        )

    weekly_zone["heart_rate_zone"] = pd.Categorical(
        weekly_zone["heart_rate_zone"],
        categories=["light", "moderate", "intense", "peak", "unknown"],
        ordered=True,
    )
    return weekly_zone


def _status_from_activity_level(level: float) -> str:
    if level <= 25:
        return "Sedentary"
    if level <= 50:
        return "Lightly Active"
    if level <= 75:
        return "Active"
    return "Very Active"


def _reset_filters_to_defaults() -> None:
    """
    Reset widget state to defaults. This works because Streamlit widgets are
    driven by st.session_state values keyed by `key=...`.
    """
    st.session_state[KEY_SHOW_CHECKS] = True
    st.session_state[KEY_SHOW_PREVIEW] = False
    st.session_state[KEY_TREND_GRANULARITY] = "Daily"
    st.session_state[KEY_STATUS_COUNT_MODE] = "Days"

    # Data source defaults
    st.session_state[KEY_DATA_SOURCE] = "Processed file"
    st.session_state[KEY_ENRICHED_PATH] = str(DEFAULT_ENRICHED_CSV)
    st.session_state.pop(KEY_UPLOAD, None)  # clear uploaded file if any

    # Filter defaults: clear date range override so we re-default to full span
    st.session_state.pop(KEY_DATE_RANGE, None)

    # HR zone widget defaults
    st.session_state[KEY_HR_GRANULARITY] = "Daily"
    st.session_state[KEY_HR_METRIC] = "Exercise Days"


def main() -> None:
    st.set_page_config(page_title="PAOS Dashboard", layout="wide")
    st.title("PAOS Dashboard (v2)")

    st.write(
        "This dashboard loads the **enriched PAOS CSV** and helps you explore activity + energy trends."
    )

    # -----------------------
    # Sidebar: Reset button
    # -----------------------
    st.sidebar.header("Controls")
    if st.sidebar.button("Reset filters", type="secondary"):
        _reset_filters_to_defaults()
        st.rerun()

    st.sidebar.header("Options")
    show_checks = st.sidebar.checkbox(
        "Show data checks", value=True, key=KEY_SHOW_CHECKS
    )
    show_preview = st.sidebar.checkbox(
        "Show data preview", value=False, key=KEY_SHOW_PREVIEW
    )
    trend_granularity = st.sidebar.selectbox(
        "Trend granularity", ["Daily", "Weekly"], key=KEY_TREND_GRANULARITY
    )
    status_count_mode = st.sidebar.selectbox(
        "Status counts by", ["Days", "Weeks"], key=KEY_STATUS_COUNT_MODE
    )

    cfg = DashboardDataConfig()

    # -----------------------
    # Data source
    # -----------------------
    st.sidebar.header("Data")
    data_source = st.sidebar.radio(
        "Data source",
        ["Processed file", "Upload CSV"],
        index=0,
        key=KEY_DATA_SOURCE,
    )

    try:
        if data_source == "Processed file":
            csv_path_str = st.sidebar.text_input(
                "Enriched CSV path",
                value=str(DEFAULT_ENRICHED_CSV),
                key=KEY_ENRICHED_PATH,
            )
            csv_path = Path(csv_path_str)
            df = _load_cached(str(csv_path))

        else:
            uploaded = st.sidebar.file_uploader(
                "Upload an enriched PAOS CSV",
                type=["csv"],
                accept_multiple_files=False,
                key=KEY_UPLOAD,
            )

            if uploaded is None:
                st.info("Upload an enriched CSV to continue.")
                st.stop()

            df = _load_uploaded_cached(uploaded.getvalue())

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

        if "date" in df.columns and df["date"].isna().all() and len(df) > 0:
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

        # Use a key so Reset can clear it
        start, end = st.date_input(
            "Date range",
            value=(min_date, max_date),
            key=KEY_DATE_RANGE,
        )

        start_ts = pd.Timestamp(start) if start else None
        end_ts = pd.Timestamp(end) if end else None

        filtered = _filter_cached(filtered, start=start_ts, end=end_ts)

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
    # Correlation (filtered)
    # -----------------------
    st.subheader("Correlation (filtered)")

    if {"activity_level", "energy_focus"}.issubset(filtered.columns) and len(filtered) > 1:
        corr_df = filtered[["activity_level", "energy_focus"]].dropna()

        if len(corr_df) > 1:
            r = corr_df["activity_level"].corr(corr_df["energy_focus"])
            st.metric("Pearson r (Activity vs Energy)", f"{r:.3f}")
        else:
            st.info("Not enough non-missing rows to compute correlation.")
    else:
        st.info("Correlation needs `activity_level` and `energy_focus`, with at least 2 rows.")

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

        if trend_granularity == "Weekly":
            weekly = _weekly_activity_trend(chart_df)
            fig = px.line(weekly, x="date", y="activity_level", markers=True)
        else:
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

        color_col = "lifestyle_status" if "lifestyle_status" in scatter_df.columns else None

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

    if len(filtered) > 0:
        if (
            status_count_mode == "Weeks"
            and "date" in filtered.columns
            and "activity_level" in filtered.columns
        ):
            counts = _weekly_status_counts(filtered)
            fig3 = px.bar(
                counts,
                x="lifestyle_status",
                y="weeks",
                category_orders={"lifestyle_status": STATUS_ORDER},
            )
            st.plotly_chart(fig3, use_container_width=True)

        elif "lifestyle_status" in filtered.columns:
            counts = filtered["lifestyle_status"].dropna().value_counts().reset_index()
            counts.columns = ["lifestyle_status", "days"]
            fig3 = px.bar(
                counts,
                x="lifestyle_status",
                y="days",
                category_orders={"lifestyle_status": STATUS_ORDER},
            )
            st.plotly_chart(fig3, use_container_width=True)

        else:
            st.info(
                "Status chart needs `lifestyle_status`, or (`date` + `activity_level`) for weekly mode."
            )
    else:
        st.info("Status chart needs data (current filter is empty).")

    # -----------------------
    # Heart Rate Zone Breakdown
    # -----------------------
    st.subheader("Heart Rate Zone Breakdown")

    if {"did_exercise", "heart_rate_zone"}.issubset(filtered.columns) and len(filtered) > 0:
        hr_granularity = st.radio(
            "Granularity",
            options=["Daily", "Weekly"],
            horizontal=True,
            key=KEY_HR_GRANULARITY,
        )

        metric_label = st.radio(
            "Measure",
            options=["Exercise Days", "Exercise Minutes"],
            horizontal=True,
            key=KEY_HR_METRIC,
        )
        metric = "days" if metric_label == "Exercise Days" else "minutes"

        if hr_granularity == "Daily":
            zone_df = hr_zone_breakdown(filtered, metric=metric)
            fig_zone = px.bar(zone_df, x="heart_rate_zone", y="value")
            st.plotly_chart(fig_zone, use_container_width=True)

        else:
            if "date" not in filtered.columns or filtered["date"].isna().all():
                st.info("Weekly HR zone view needs a valid `date` column.")
            else:
                weekly_zone = _weekly_hr_zone(filtered, metric=metric)
                fig_zone = px.bar(
                    weekly_zone,
                    x="date",
                    y="value",
                    color="heart_rate_zone",
                    barmode="stack",
                )
                st.plotly_chart(fig_zone, use_container_width=True)
    else:
        st.info("HR zone chart needs `did_exercise` and `heart_rate_zone` data.")

    # -----------------------
    # Preview
    # -----------------------
    if show_preview:
        st.subheader("Data preview")
        st.dataframe(filtered, width="stretch")


if __name__ == "__main__":
    main()

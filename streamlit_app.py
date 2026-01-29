from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


DEFAULT_ENRICHED_CSV = Path("data/processed/daily_log_enriched.csv")


@st.cache_data
def load_enriched_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Enriched CSV not found: {path}")
    return pd.read_csv(path)


def main() -> None:
    st.set_page_config(page_title="PAOS Dashboard", layout="wide")
    st.title("PAOS Dashboard (v2)")

    st.write(
        "This dashboard loads the **enriched PAOS CSV** and helps you explore activity + energy trends."
    )

    csv_path_str = st.text_input("Enriched CSV path", value=str(DEFAULT_ENRICHED_CSV))
    csv_path = Path(csv_path_str)

    try:
        df = load_enriched_csv(csv_path)
    except FileNotFoundError:
        st.error(
            f"Could not find the enriched CSV at: `{csv_path}`\n\n"
            "Run:\n"
            "`python scripts/paos_run.py transform --input-type csv --input data/sample/daily_log.csv "
            "--processed data/processed/daily_log_enriched.csv`"
        )
        st.stop()

    # Basic cleanup for date filtering (if date exists)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    st.subheader("Quick metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Days logged", len(df))

    with col2:
        if "activity_level" in df.columns:
            st.metric("Avg Activity Level", f"{df['activity_level'].mean():.1f}")
        else:
            st.metric("Avg Activity Level", "N/A")

    with col3:
        if "energy_focus" in df.columns:
            st.metric("Avg Energy/Focus", f"{df['energy_focus'].mean():.2f}")
        else:
            st.metric("Avg Energy/Focus", "N/A")

    st.subheader("Filter")

    filtered = df.copy()

    if "date" in filtered.columns and filtered["date"].notna().any():
        min_date = filtered["date"].min().date()
        max_date = filtered["date"].max().date()

        start, end = st.date_input("Date range", value=(min_date, max_date))

        filtered = filtered[
            (filtered["date"].dt.date >= start) & (filtered["date"].dt.date <= end)
        ]

    st.subheader("Data preview")
    st.dataframe(filtered, width="stretch")


if __name__ == "__main__":
    main()

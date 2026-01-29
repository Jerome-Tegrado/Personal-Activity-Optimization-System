from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


DEFAULT_ENRICHED_CSV = Path("data/processed/daily_log_enriched.csv")

REQUIRED_COLUMNS = ("date", "steps", "energy_focus", "activity_level")


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

    # Date parsing (if date exists)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # -----------------------
    # Data checks (friendly)
    # -----------------------
    st.subheader("Data checks")

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.warning(
            "Some expected columns are missing:\n\n"
            + "\n".join([f"- `{c}`" for c in missing])
        )
        st.info(
            "This can happen if you loaded a non-enriched CSV. "
            "Try generating the enriched file using the transform stage."
        )
    else:
        st.success("Looks good — expected columns found.")

    if "date" in df.columns:
        if df["date"].isna().all() and len(df) > 0:
            st.warning(
                "The `date` column exists, but none of the values could be parsed as valid dates."
            )

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

    st.subheader("Filter")

    filtered = df.copy()

    if "date" in filtered.columns and filtered["date"].notna().any():
        min_date = filtered["date"].min().date()
        max_date = filtered["date"].max().date()

        start, end = st.date_input("Date range", value=(min_date, max_date))

        filtered = filtered[
            (filtered["date"].dt.date >= start) & (filtered["date"].dt.date <= end)
        ]

    if filtered.empty:
        st.info("No rows to show (empty dataset or date range filter returned 0 rows).")

    st.subheader("Data preview")
    st.dataframe(filtered, width="stretch")


if __name__ == "__main__":
    main()

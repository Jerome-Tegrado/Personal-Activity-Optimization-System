from __future__ import annotations

import pandas as pd

from paos.ingest import apply_optional_hr_columns


def ingest_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]

    # Keep as pandas datetime64[ns] (not Python datetime.date objects)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df["steps"] = pd.to_numeric(df["steps"], errors="coerce")
    df["energy_focus"] = pd.to_numeric(df["energy_focus"], errors="coerce")

    df["did_exercise"] = df["did_exercise"].astype(str).str.strip().str.lower()
    df["did_exercise"] = df["did_exercise"].map({"yes": True, "no": False}).fillna(False)

    for col in ["exercise_type", "exercise_minutes", "heart_rate_zone", "notes"]:
        if col not in df.columns:
            df[col] = pd.NA

    df["exercise_minutes"] = pd.to_numeric(df["exercise_minutes"], errors="coerce")
    df["heart_rate_zone"] = df["heart_rate_zone"].astype("string").str.strip().str.lower()

    # v3 Section 2 Step 1: optional HR inputs (no-op if absent)
    df = apply_optional_hr_columns(df)

    # Keep the latest row for each date (based on file order)
    df = df.dropna(subset=["date"]).drop_duplicates(subset=["date"], keep="last")

    return df.sort_values("date").reset_index(drop=True)

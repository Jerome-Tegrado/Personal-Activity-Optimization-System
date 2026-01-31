from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import pandas as pd


# ---------------------------
# v3 Section 2 (Step 1)
# Optional HR input support
# ---------------------------

_HR_RENAME_MAP: dict[str, str] = {
    # average HR variants -> canonical
    "avg_hr": "avg_hr_bpm",
    "average_hr": "avg_hr_bpm",
    "avg_bpm": "avg_hr_bpm",
    "average_bpm": "avg_hr_bpm",
    "avg_hr_bpm": "avg_hr_bpm",
    # time-in-zone minutes variants -> canonical
    "mins_light": "minutes_light",
    "mins_moderate": "minutes_moderate",
    "mins_intense": "minutes_intense",
    "mins_peak": "minutes_peak",
    "minutes_light": "minutes_light",
    "minutes_moderate": "minutes_moderate",
    "minutes_intense": "minutes_intense",
    "minutes_peak": "minutes_peak",
}


def apply_optional_hr_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize optional heart-rate input columns (v3 Section 2 Step 1).

    Supported (optional):
      - avg_hr_bpm
      - minutes_light / minutes_moderate / minutes_intense / minutes_peak

    Behavior:
      - If these columns are present (or present under known variants), they are renamed
        to canonical names and coerced to numeric.
      - If they are absent, this is a no-op.
      - Blank strings become NaN.
    """
    if df is None or df.empty:
        return df

    # Rename known variants -> canonical names (only for columns that exist)
    rename_map = {c: _HR_RENAME_MAP[c] for c in df.columns if c in _HR_RENAME_MAP}
    if rename_map:
        df = df.rename(columns=rename_map)

    # Coerce numeric if present
    hr_cols = ["avg_hr_bpm", "minutes_light", "minutes_moderate", "minutes_intense", "minutes_peak"]
    for col in hr_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def load_daily_log(source: str, **kwargs: Any) -> pd.DataFrame:
    """
    Unified ingestion entrypoint for PAOS.

    source:
      - "csv"
      - "sheets"

    kwargs for csv:
      - path: str | Path (required)

    kwargs for sheets:
      - spreadsheet_id: str (required)
      - range_: str (required)
      - credentials_path: str (optional)
      - token_path: str (optional)
      - dump_raw_path: str | Path (optional)  # writes raw Sheets snapshot before cleaning
    """
    source = source.strip().lower()

    if source == "csv":
        path = kwargs.get("path")
        if path is None:
            raise ValueError('CSV ingestion requires "path="')

        import paos.ingest.csv_ingest as csv_ingest

        for name in ("ingest_csv", "read_daily_log_csv", "load_daily_log_csv", "read_csv"):
            fn = getattr(csv_ingest, name, None)
            if callable(fn):
                return fn(Path(path))

        raise RuntimeError("No CSV ingest function found in paos.ingest.csv_ingest")

    if source == "sheets":
        spreadsheet_id: Optional[str] = kwargs.get("spreadsheet_id")
        range_: Optional[str] = kwargs.get("range_")
        if not spreadsheet_id or not range_:
            raise ValueError('Sheets ingestion requires "spreadsheet_id=" and "range_="')

        from paos.ingest.sheets_ingest import SheetsConfig, read_daily_log_from_sheets

        cfg = SheetsConfig(
            spreadsheet_id=spreadsheet_id,
            range_=range_,
            credentials_path=kwargs.get("credentials_path", "secrets/credentials.json"),
            token_path=kwargs.get("token_path", "secrets/token.json"),
        )

        dump_raw_path = kwargs.get("dump_raw_path")
        return read_daily_log_from_sheets(cfg, dump_raw_path=dump_raw_path)

    raise ValueError(f"Unknown source: {source}. Expected 'csv' or 'sheets'.")

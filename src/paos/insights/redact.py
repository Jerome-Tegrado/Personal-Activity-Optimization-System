from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import pandas as pd


@dataclass(frozen=True)
class RedactConfig:
    """
    Privacy configuration for producing a public-safe dataframe.

    - drop_notes: remove the 'notes' column if present
    - bucket_dates_to_week: replace date with a week key like '2026-W01'
    - keep_columns: if provided, only keep these columns (after redaction)
    """
    date_col: str = "date"
    drop_notes: bool = True
    notes_col: str = "notes"
    bucket_dates_to_week: bool = False
    week_col: str = "week"
    keep_columns: Optional[list[str]] = None


def _to_week_key(dt: pd.Timestamp) -> str:
    # ISO year/week (more stable for week reporting)
    iso = dt.isocalendar()
    return f"{int(iso.year)}-W{int(iso.week):02d}"


def redact_dataframe(df: pd.DataFrame, cfg: RedactConfig | None = None) -> pd.DataFrame:
    """
    Return a privacy-safe copy of df.

    Rules:
    - Optionally drop notes
    - Optionally replace date with a week bucket column (and drop raw date)
    - Optionally restrict to keep_columns
    """
    cfg = cfg or RedactConfig()
    out = df.copy()

    # Drop notes (public-safe default)
    if cfg.drop_notes and cfg.notes_col in out.columns:
        out = out.drop(columns=[cfg.notes_col])

    # Bucket date -> week key (optional)
    if cfg.bucket_dates_to_week and cfg.date_col in out.columns:
        dt = pd.to_datetime(out[cfg.date_col], errors="coerce")
        out[cfg.week_col] = dt.map(lambda x: _to_week_key(x) if pd.notna(x) else pd.NA)
        out = out.drop(columns=[cfg.date_col])

    # Optionally keep only a known-safe set of columns
    if cfg.keep_columns is not None:
        existing = [c for c in cfg.keep_columns if c in out.columns]
        out = out[existing].copy()

    return out

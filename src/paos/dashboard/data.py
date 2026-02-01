from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any

import pandas as pd

DEFAULT_REQUIRED_COLUMNS = [
    "date",
    "steps",
    "energy_focus",
    "did_exercise",
    "activity_level",
    "lifestyle_status",
]

HR_ZONE_ORDER = ["light", "moderate", "intense", "peak", "unknown"]


@dataclass(frozen=True)
class DashboardDataConfig:
    required_columns: list[str] | None = None

    def __post_init__(self) -> None:
        if self.required_columns is None:
            object.__setattr__(self, "required_columns", list(DEFAULT_REQUIRED_COLUMNS))


def load_enriched_csv(path_or_file: str | Path | IO[Any]) -> pd.DataFrame:
    """
    Load the enriched CSV the dashboard reads.

    Supports:
      - str / Path (filesystem path)
      - file-like objects (e.g., io.BytesIO from Streamlit uploader)
    """
    # File-like object
    if hasattr(path_or_file, "read"):
        return pd.read_csv(path_or_file)

    path = Path(path_or_file)
    if not path.exists():
        raise FileNotFoundError(f"Enriched CSV not found: {path}")
    return pd.read_csv(path)


def validate_required_columns(df: pd.DataFrame, required: list[str]) -> None:
    """Raise if required columns are missing."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def coerce_date_column(df: pd.DataFrame, col: str = "date") -> pd.DataFrame:
    """Parse df[col] into datetime; invalid values become NaT."""
    out = df.copy()
    if col in out.columns:
        out[col] = pd.to_datetime(out[col], errors="coerce")
    return out


def filter_by_date_range(
    df: pd.DataFrame,
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
    col: str = "date",
) -> pd.DataFrame:
    """Inclusive date filtering."""
    out = df
    if col not in out.columns:
        return out
    if start is not None:
        out = out[out[col] >= start]
    if end is not None:
        out = out[out[col] <= end]
    return out


def hr_zone_breakdown(df: pd.DataFrame, metric: str = "days") -> pd.DataFrame:
    """
    Summarize heart_rate_zone for exercised days with stable ordering.

    metric:
      - "days": count exercised rows per zone
      - "minutes": sum exercise_minutes per zone
    """
    if metric not in {"days", "minutes"}:
        raise ValueError("metric must be 'days' or 'minutes'")

    # Always return stable categories
    if df is None or df.empty:
        out = pd.DataFrame({"heart_rate_zone": HR_ZONE_ORDER, "value": [0] * len(HR_ZONE_ORDER)})
        out["heart_rate_zone"] = pd.Categorical(
            out["heart_rate_zone"], categories=HR_ZONE_ORDER, ordered=True
        )
        return out

    dfx = df.copy()

    if "did_exercise" not in dfx.columns or "heart_rate_zone" not in dfx.columns:
        out = pd.DataFrame({"heart_rate_zone": HR_ZONE_ORDER, "value": [0] * len(HR_ZONE_ORDER)})
        out["heart_rate_zone"] = pd.Categorical(
            out["heart_rate_zone"], categories=HR_ZONE_ORDER, ordered=True
        )
        return out

    # Keep only exercised rows
    did = dfx["did_exercise"].astype(str).str.strip().str.lower()
    dfx = dfx[did == "yes"]

    # Normalize zones
    dfx["heart_rate_zone"] = (
        dfx["heart_rate_zone"]
        .astype(str)
        .str.strip()
        .str.lower()
        .replace({"nan": "unknown", "none": "unknown", "": "unknown"})
    )

    if metric == "days":
        s = dfx.groupby("heart_rate_zone").size()
    else:
        mins = pd.to_numeric(dfx.get("exercise_minutes"), errors="coerce").fillna(0)
        s = mins.groupby(dfx["heart_rate_zone"]).sum()

    s = s.reindex(HR_ZONE_ORDER, fill_value=0)

    out = s.reset_index()
    out.columns = ["heart_rate_zone", "value"]
    out["heart_rate_zone"] = pd.Categorical(
        out["heart_rate_zone"], categories=HR_ZONE_ORDER, ordered=True
    )
    return out

# src/paos/ingest/sheets_ingest.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from paos.ingest import apply_optional_hr_columns

SCOPES: List[str] = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


@dataclass(frozen=True)
class SheetsConfig:
    spreadsheet_id: str
    range_: str
    credentials_path: str = "secrets/credentials.json"
    token_path: str = "secrets/token.json"


def get_creds(credentials_path: str, token_path: str) -> Credentials:
    creds: Optional[Credentials] = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return creds


def fetch_values(cfg: SheetsConfig) -> list[list[str]]:
    creds = get_creds(cfg.credentials_path, cfg.token_path)
    service = build("sheets", "v4", credentials=creds)
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=cfg.spreadsheet_id, range=cfg.range_)
        .execute()
    )
    return result.get("values", [])


def read_daily_log_from_sheets(
    cfg: SheetsConfig,
    dump_raw_path: str | Path | None = None,
) -> pd.DataFrame:
    values = fetch_values(cfg)
    if not values:
        return pd.DataFrame()

    headers = values[0]
    rows = values[1:]

    # RAW snapshot (exactly as returned by Sheets)
    df_raw = pd.DataFrame(rows, columns=headers)

    if dump_raw_path is not None:
        dump_path = Path(dump_raw_path)
        dump_path.parent.mkdir(parents=True, exist_ok=True)
        df_raw.to_csv(dump_path, index=False)

    # Continue processing from raw
    df = df_raw.copy()

    # Map Google Form headers -> PAOS internal column names
    rename_map = {
        "Timestamp": "timestamp",
        "Date": "date",
        "Steps": "steps",
        "Energy/Focus": "energy_focus",
        "Did you exercise today?": "did_exercise",
        "Exercise Type": "exercise_type",
        "Exercise Minutes": "exercise_minutes",
        "Heart Rate Zone": "heart_rate_zone",
        "Notes": "notes",
        # If you later add "Start Time", include it here
        "Start Time": "start_time",
        # (Optional) If you later add HR inputs to the form/sheet, map them here too
        "Avg HR BPM": "avg_hr_bpm",
        "Minutes Light": "minutes_light",
        "Minutes Moderate": "minutes_moderate",
        "Minutes Intense": "minutes_intense",
        "Minutes Peak": "minutes_peak",
    }
    df = df.rename(columns=rename_map)

    # --- Clean types/values ---

    # timestamp -> datetime (used for dedupe)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # date -> YYYY-MM-DD string (stable key)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")

    # steps: remove commas/spaces -> int
    if "steps" in df.columns:
        df["steps"] = df["steps"].astype(str).str.replace(",", "", regex=False).str.strip()
        df["steps"] = pd.to_numeric(df["steps"], errors="coerce").astype("Int64")

    # energy_focus -> int
    if "energy_focus" in df.columns:
        df["energy_focus"] = pd.to_numeric(df["energy_focus"], errors="coerce").astype("Int64")

    # exercise_minutes -> int (blank allowed)
    if "exercise_minutes" in df.columns:
        df["exercise_minutes"] = pd.to_numeric(df["exercise_minutes"], errors="coerce").astype("Int64")

    # did_exercise normalize to "Yes"/"No"
    if "did_exercise" in df.columns:
        df["did_exercise"] = df["did_exercise"].astype(str).str.strip().str.title()
        df.loc[~df["did_exercise"].isin(["Yes", "No"]), "did_exercise"] = pd.NA

    # heart_rate_zone normalize from verbose labels -> paos categories
    if "heart_rate_zone" in df.columns:
        z = df["heart_rate_zone"].astype(str).str.strip().str.lower()

        def _map_zone(val: str) -> str:
            if not val or val == "nan":
                return ""
            if val.startswith("light"):
                return "light"
            if val.startswith("moderate"):
                return "moderate"
            if val.startswith("intense"):
                return "intense"
            if val.startswith("peak"):
                return "peak"
            if "unknown" in val:
                return "unknown"
            return ""

        df["heart_rate_zone"] = z.map(_map_zone)
        df.loc[df["heart_rate_zone"] == "", "heart_rate_zone"] = pd.NA

    # v3 Section 2 Step 1: optional HR inputs (no-op if absent)
    df = apply_optional_hr_columns(df)

    # --- Dedupe: keep latest submission per date ---
    if "date" in df.columns and "timestamp" in df.columns:
        df = (
            df.sort_values("timestamp")
            .drop_duplicates(subset=["date"], keep="last")
            .reset_index(drop=True)
        )

    return df

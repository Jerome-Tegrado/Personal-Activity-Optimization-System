# src/paos/ingest/sheets_ingest.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

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


def read_daily_log_from_sheets(cfg: SheetsConfig) -> pd.DataFrame:
    values = fetch_values(cfg)
    if not values:
        return pd.DataFrame()

    headers = values[0]
    rows = values[1:]
    df = pd.DataFrame(rows, columns=headers)

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
    }
    df = df.rename(columns=rename_map)

    return df

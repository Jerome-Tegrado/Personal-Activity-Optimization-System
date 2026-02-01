from __future__ import annotations

import os

from paos.ingest.sheets_ingest import SheetsConfig, read_daily_log_from_sheets


def main() -> None:
    spreadsheet_id = os.getenv("PAOS_SHEETS_ID")
    if not spreadsheet_id:
        raise SystemExit(
            "Missing PAOS_SHEETS_ID env var.\n"
            "PowerShell example:\n"
            '  $env:PAOS_SHEETS_ID="YOUR_SHEET_ID"\n'
            "  python scripts/sheets_to_df_demo.py"
        )

    range_ = os.getenv("PAOS_SHEETS_RANGE", "Form Responses 1!A1:J20")

    cfg = SheetsConfig(
        spreadsheet_id=spreadsheet_id,
        range_=range_,
    )

    df = read_daily_log_from_sheets(cfg)
    print(df.head())
    print(df.columns.tolist())


if __name__ == "__main__":
    main()

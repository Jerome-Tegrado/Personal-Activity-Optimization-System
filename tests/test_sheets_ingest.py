import pandas as pd

import paos.ingest.sheets_ingest as sheets_ingest
from paos.ingest.sheets_ingest import SheetsConfig


def test_read_daily_log_from_sheets_normalizes_and_dedupes(monkeypatch):
    # Fake "values" as returned by Google Sheets API
    values = [
        [
            "Timestamp",
            "Date",
            "Steps",
            "Energy/Focus",
            "Did you exercise today?",
            "Exercise Type",
            "Start Time",
            "Exercise Minutes",
            "Heart Rate Zone",
            "Notes",
        ],
        # Older submission for same date
        [
            "1/25/2026 15:00:00",
            "1/25/2026",
            "8,000",
            "3",
            "Yes",
            "cardio",
            "11:00:00 PM",
            "20",
            "Moderate (119-139 bpm)",
            "older",
        ],
        # Newer submission for same date (should win after dedupe)
        [
            "1/25/2026 15:47:03",
            "1/25/2026",
            "8,670",
            "4",
            "Yes",
            "strength",
            "11:27:00 PM",
            "32",
            "Intense (139-168 bpm)",
            "newer",
        ],
        # Another day, no exercise fields
        [
            "1/25/2026 15:47:46",
            "1/24/2026",
            "1,360",
            "2",
            "No",
            "",
            "",
            "",
            "",
            "rest day",
        ],
    ]

    def fake_fetch_values(cfg: SheetsConfig):
        return values

    monkeypatch.setattr(sheets_ingest, "fetch_values", fake_fetch_values)

    cfg = SheetsConfig(spreadsheet_id="dummy", range_="dummy")
    df = sheets_ingest.read_daily_log_from_sheets(cfg)

    # After dedupe: expect 2 rows (2026-01-24 and 2026-01-25)
    assert len(df) == 2
    assert set(df["date"].tolist()) == {"2026-01-24", "2026-01-25"}

    # Find the 2026-01-25 row (should be newer submission)
    row_25 = df.loc[df["date"] == "2026-01-25"].iloc[0]

    assert row_25["steps"] == 8670
    assert row_25["energy_focus"] == 4
    assert row_25["exercise_minutes"] == 32
    assert row_25["heart_rate_zone"] == "intense"
    assert row_25["notes"] == "newer"

    # Check 2026-01-24 row parsing
    row_24 = df.loc[df["date"] == "2026-01-24"].iloc[0]
    assert row_24["steps"] == 1360
    assert row_24["energy_focus"] == 2
    assert pd.isna(row_24["exercise_minutes"])
    assert pd.isna(row_24["heart_rate_zone"]) or row_24["heart_rate_zone"] == ""

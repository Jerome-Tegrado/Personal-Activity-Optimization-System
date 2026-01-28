from __future__ import annotations

from pathlib import Path

import pandas as pd

import paos.ingest


_REAL_LOAD_DAILY_LOG = paos.ingest.load_daily_log


def _fake_load_daily_log(source: str, **kwargs):
    source = source.strip().lower()

    if source == "sheets":
        # Cleaned DF returned to pipeline (PAOS schema)
        df_clean = pd.DataFrame(
            {
                "date": ["2026-01-01"],
                "steps": [8000],
                "energy_focus": [4],
                "did_exercise": ["No"],
                "exercise_type": [None],
                "exercise_minutes": [None],
                "heart_rate_zone": [None],
                "notes": [None],
            }
        )

        dump_raw_path = kwargs.get("dump_raw_path")
        if dump_raw_path:
            # Raw-ish snapshot similar to Google Forms → Sheets export
            df_raw = pd.DataFrame(
                {
                    "Timestamp": ["1/1/2026 08:00:00"],
                    "Date": ["2026-01-01"],
                    "Steps": ["8,000"],
                    "Energy/Focus": ["4"],
                    "Did you exercise today?": ["No"],
                    "Exercise Type": [""],
                    "Exercise Duration (minutes)": [""],
                    "Heart Rate Zone": [""],
                    "Notes": [""],
                }
            )

            p = Path(dump_raw_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            df_raw.to_csv(p, index=False)

        return df_clean

    # IMPORTANT: call the original for csv/other sources (avoid recursion)
    return _REAL_LOAD_DAILY_LOG(source, **kwargs)


paos.ingest.load_daily_log = _fake_load_daily_log

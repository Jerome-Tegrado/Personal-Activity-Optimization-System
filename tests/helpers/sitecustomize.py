from __future__ import annotations

from pathlib import Path

import pandas as pd

import paos.ingest


def _fake_load_daily_log(source: str, **kwargs):
    source = source.strip().lower()
    if source == "sheets":
        df = pd.DataFrame(
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
            p = Path(dump_raw_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(p, index=False)

        return df

    # IMPORTANT: call the original for csv (avoid recursion)
    return _REAL_LOAD_DAILY_LOG(source, **kwargs)


_REAL_LOAD_DAILY_LOG = paos.ingest.load_daily_log
paos.ingest.load_daily_log = _fake_load_daily_log

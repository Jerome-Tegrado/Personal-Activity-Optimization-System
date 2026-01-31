from pathlib import Path

import pandas as pd

from paos.ingest import load_daily_log


def test_csv_ingest_supports_optional_hr_columns(tmp_path: Path):
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "steps": [7000, 8000, 9000],
            "energy_focus": [3, 4, 2],
            "did_exercise": ["Yes", "No", "Yes"],
            # new optional HR inputs (strings on purpose, to test coercion)
            "avg_hr_bpm": ["145", "", "170"],
            "minutes_light": ["10", "", "0"],
            "minutes_moderate": ["20", "", "15"],
            "minutes_intense": ["0", "", "20"],
            "minutes_peak": ["0", "", "5"],
        }
    )

    p = tmp_path / "hr_input.csv"
    df.to_csv(p, index=False)

    out = load_daily_log("csv", path=p)

    for c in ["avg_hr_bpm", "minutes_light", "minutes_moderate", "minutes_intense", "minutes_peak"]:
        assert c in out.columns

    # numeric coercion checks
    assert pd.api.types.is_numeric_dtype(out["avg_hr_bpm"])
    assert pd.api.types.is_numeric_dtype(out["minutes_light"])

    # blank string -> NaN
    assert pd.isna(out.loc[1, "avg_hr_bpm"])

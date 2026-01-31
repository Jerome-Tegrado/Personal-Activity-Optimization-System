from pathlib import Path

import pandas as pd

from paos.ingest import load_daily_log
from paos.transform.scoring import enrich


def test_hr_zone_inference_pipeline_from_csv_avg_hr(tmp_path: Path):
    # heart_rate_zone missing, but avg_hr_bpm present
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02"],
            "steps": [6000, 7000],
            "energy_focus": [3, 4],
            "did_exercise": ["Yes", "No"],
            "exercise_minutes": [40, ""],
            "heart_rate_zone": ["", ""],
            "avg_hr_bpm": [150, ""],  # should infer using default max_hr=198
            "notes": ["", ""],
        }
    )

    p = tmp_path / "daily.csv"
    df.to_csv(p, index=False)

    raw = load_daily_log("csv", path=p)
    out = enrich(raw)

    # Exercise day should have inferred zone and exercise points > 0
    assert bool(out.loc[0, "did_exercise"]) is True
    assert pd.notna(out.loc[0, "heart_rate_zone"])
    assert out.loc[0, "exercise_points"] > 0

    # Rest day should not force a zone
    assert bool(out.loc[1, "did_exercise"]) is False

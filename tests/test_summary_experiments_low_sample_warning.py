from pathlib import Path

import pandas as pd

from paos.analysis.summary import write_weekly_summary


def test_weekly_summary_experiments_warns_on_low_sample(tmp_path: Path, monkeypatch):
    """
    Explicitly verifies the '⚠️ low sample' warning when either control or treatment
    has <2 samples in the slice.
    """
    monkeypatch.chdir(tmp_path)

    spec_dir = tmp_path / "data" / "sample"
    spec_dir.mkdir(parents=True, exist_ok=True)

    spec_path = spec_dir / "experiments.csv"
    spec_path.write_text(
        "\n".join(
            [
                "experiment,start_date,end_date,phase,label",
                "e,2026-01-01,2026-01-03,control,baseline",
                "e,2026-01-04,2026-01-04,treatment,test",
            ]
        ),
        encoding="utf-8",
    )

    # 4-day week slice ending 2026-01-04:
    # control days = 3, treatment days = 1 -> should warn
    df = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=4, freq="D").astype(str),
            "activity_level": [40, 42, 44, 60],
            "energy_focus": [2, 2, 3, 4],
            "did_exercise": ["Yes"] * 4,
            "lifestyle_status": ["Sedentary"] * 4,
        }
    )

    out_path = tmp_path / "summary.md"
    write_weekly_summary(df, out_path, week_end="2026-01-04", experiments_spec=spec_path)

    text = out_path.read_text(encoding="utf-8").lower()
    assert "experiments" in text
    assert "low sample" in text

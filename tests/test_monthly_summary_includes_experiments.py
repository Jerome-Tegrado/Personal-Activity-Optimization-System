from pathlib import Path

import pandas as pd

from paos.analysis.summary import write_monthly_summary


def test_monthly_summary_includes_experiments_when_spec_provided(tmp_path: Path):
    # Build a month of data with two windows: control then treatment
    df = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=10, freq="D").astype(str),
            "steps": [8000, 8200, 8300, 8400, 8500, 9500, 9600, 9700, 9800, 9900],
            "activity_level": [40, 41, 42, 43, 44, 60, 61, 62, 63, 64],
            "energy_focus": [2, 2, 3, 3, 3, 4, 4, 4, 5, 5],
            "did_exercise": ["Yes"] * 10,
            "lifestyle_status": ["Sedentary"] * 10,
        }
    )

    spec_path = tmp_path / "experiments.csv"
    spec_path.write_text(
        "\n".join(
            [
                "experiment,start_date,end_date,phase,label",
                "e,2026-01-01,2026-01-05,control,baseline",
                "e,2026-01-06,2026-01-31,treatment,test",
            ]
        ),
        encoding="utf-8",
    )

    out_path = tmp_path / "monthly.md"
    write_monthly_summary(df, out_path, month="2026-01", experiments_spec=spec_path)

    text = out_path.read_text(encoding="utf-8")
    assert "## Experiments" in text
    assert "### e" in text

    # Verdict marker should appear for at least one metric line
    assert "— **" in text

    verdict_phrases = [
        "likely improvement",
        "likely worse",
        "possible improvement",
        "possible worse",
        "unclear",
    ]
    assert any(v in text.lower() for v in verdict_phrases)


def test_monthly_summary_skips_experiments_when_not_provided(tmp_path: Path):
    df = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=7, freq="D").astype(str),
            "steps": [8000] * 7,
            "activity_level": [10, 20, 30, 40, 50, 60, 70],
            "energy_focus": [1, 2, 3, 4, 5, 4, 3],
            "did_exercise": ["Yes"] * 7,
            "lifestyle_status": ["Sedentary"] * 7,
        }
    )

    out_path = tmp_path / "monthly.md"
    write_monthly_summary(df, out_path, month="2026-01", experiments_spec=None)

    text = out_path.read_text(encoding="utf-8")
    assert "## Experiments" not in text

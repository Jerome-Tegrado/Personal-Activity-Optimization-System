from pathlib import Path

import pandas as pd

from paos.analysis.summary import write_weekly_summary


def test_weekly_summary_includes_experiments_section_when_spec_exists(tmp_path: Path):
    spec_dir = tmp_path / "data" / "sample"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_path = spec_dir / "experiments.csv"

    spec_path.write_text(
        "\n".join(
            [
                "experiment,start_date,end_date,phase,label",
                "lunch-walk,2026-01-01,2026-01-14,control,baseline",
                "lunch-walk,2026-01-15,2026-01-31,treatment,walk-after-lunch",
            ]
        ),
        encoding="utf-8",
    )

    # Create a 7-day window ending 2026-01-20 that includes BOTH control and treatment days
    df = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-14", periods=7, freq="D").astype(str),
            "activity_level": [40, 42, 44, 60, 62, 64, 66],
            "energy_focus": [2, 2, 3, 4, 4, 5, 5],
            "did_exercise": ["Yes"] * 7,
            "lifestyle_status": ["Sedentary"] * 7,
            "notes": ["private"] * 7,
        }
    )

    out_path = tmp_path / "summary.md"
    write_weekly_summary(df, out_path, week_end="2026-01-20", experiments_spec=spec_path)

    text = out_path.read_text(encoding="utf-8")
    assert "## Experiments" in text
    assert "### lunch-walk" in text
    assert "Activity Level" in text
    assert "Energy/Focus" in text

    # Verdict formatting marker is present
    assert "— **" in text

    # Stronger: verdict text must be one of expected labels
    verdict_phrases = [
        "likely improvement",
        "likely worse",
        "possible improvement",
        "possible worse",
        "unclear",
    ]
    assert any(v in text.lower() for v in verdict_phrases)


def test_weekly_summary_skips_experiments_section_when_spec_not_provided(tmp_path: Path):
    df = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=7, freq="D").astype(str),
            "activity_level": [10, 20, 30, 40, 50, 60, 70],
            "energy_focus": [1, 2, 3, 4, 5, 4, 3],
            "did_exercise": ["Yes"] * 7,
            "lifestyle_status": ["Sedentary"] * 7,
        }
    )

    out_path = tmp_path / "summary.md"
    write_weekly_summary(df, out_path, week_end="2026-01-07", experiments_spec=None)

    text = out_path.read_text(encoding="utf-8")
    assert "## Experiments" not in text

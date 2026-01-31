from pathlib import Path

import pandas as pd

from paos.analysis.summary import write_weekly_summary


def test_weekly_summary_includes_insights_section(tmp_path: Path):
    df = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=14, freq="D").astype(str),
            "activity_level": list(range(10, 24)),
            "energy_focus": [1, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 4, 3, 2],
            "did_exercise": ["Yes", "No"] * 7,
            "lifestyle_status": ["Sedentary"] * 14,
            "notes": ["private"] * 14,
        }
    )

    out_path = tmp_path / "summary.md"
    write_weekly_summary(df, out_path)

    text = out_path.read_text(encoding="utf-8")
    assert "## Insights" in text
    # at least one bullet insight
    assert "- **" in text

from __future__ import annotations

from pathlib import Path

import pandas as pd

from paos.analysis.summary import write_monthly_summary, write_weekly_summary


def test_weekly_summary_includes_benchmarks_when_spec_provided(tmp_path: Path):
    spec = tmp_path / "bench.csv"
    spec.write_text(
        "\n".join(
            [
                "metric,group,unit,p25,p50,p75,p90,source",
                "steps,adult,steps/day,5000,7000,9000,11000,synthetic",
                "activity_level,adult,score,30,50,70,85,synthetic",
            ]
        ),
        encoding="utf-8",
    )

    df = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-14", periods=7, freq="D").astype(str),
            "steps": [4000, 6000, 7000, 8000, 9000, 9500, 12000],
            "activity_level": [40, 42, 44, 60, 62, 64, 66],
            "energy_focus": [2, 2, 3, 4, 4, 5, 5],
            "did_exercise": ["Yes"] * 7,
            "lifestyle_status": ["Lightly Active"] * 7,
        }
    )

    out_path = tmp_path / "weekly.md"
    write_weekly_summary(
        df,
        out_path,
        week_end="2026-01-20",
        benchmarks_spec=spec,
        benchmark_group="adult",
        benchmark_metrics=("steps", "activity_level"),
    )

    text = out_path.read_text(encoding="utf-8")
    assert "## Benchmarks" in text
    assert "Steps" in text
    assert "Activity Level" in text


def test_monthly_summary_includes_benchmarks_when_spec_provided(tmp_path: Path):
    spec = tmp_path / "bench.csv"
    spec.write_text(
        "\n".join(
            [
                "metric,group,unit,p25,p50,p75,p90,source",
                "steps,adult,steps/day,5000,7000,9000,11000,synthetic",
            ]
        ),
        encoding="utf-8",
    )

    df = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=10, freq="D").astype(str),
            "steps": [5000, 5200, 5400, 7000, 7200, 9000, 9200, 9400, 11000, 12000],
            "activity_level": [35, 36, 37, 50, 51, 70, 71, 72, 80, 82],
            "energy_focus": [2, 2, 3, 3, 3, 4, 4, 4, 5, 5],
            "did_exercise": ["Yes"] * 10,
            "lifestyle_status": ["Lightly Active"] * 10,
        }
    )

    out_path = tmp_path / "monthly.md"
    write_monthly_summary(
        df,
        out_path,
        month="2026-01",
        benchmarks_spec=spec,
        benchmark_group="adult",
        benchmark_metrics=("steps",),
    )

    text = out_path.read_text(encoding="utf-8")
    assert "## Benchmarks" in text
    assert "Steps" in text


def test_weekly_summary_skips_benchmarks_when_not_provided(tmp_path: Path):
    df = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=7, freq="D").astype(str),
            "steps": [8000] * 7,
            "activity_level": [50] * 7,
            "energy_focus": [3] * 7,
            "did_exercise": ["Yes"] * 7,
            "lifestyle_status": ["Lightly Active"] * 7,
        }
    )

    out_path = tmp_path / "weekly.md"
    write_weekly_summary(df, out_path, week_end="2026-01-07", benchmarks_spec=None)

    text = out_path.read_text(encoding="utf-8")
    assert "## Benchmarks" not in text

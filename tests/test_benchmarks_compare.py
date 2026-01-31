from __future__ import annotations

from pathlib import Path

import pandas as pd

from paos.benchmarks.compare import compare_to_benchmarks


def test_compare_to_benchmarks_returns_percentile(tmp_path: Path):
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
            "date": pd.date_range("2026-01-01", periods=7, freq="D").astype(str),
            "steps": [4000, 5000, 6500, 7000, 8000, 9000, 12000],
        }
    )

    out = compare_to_benchmarks(df, spec_path=spec, group="adult", metrics=("steps",))
    assert len(out) == 1

    r = out[0]
    assert r.metric == "steps"
    assert r.group == "adult"
    assert r.unit == "steps/day"
    assert r.user_mean is not None
    assert r.user_median is not None
    assert r.approx_percentile is not None
    assert 0.0 <= r.approx_percentile <= 100.0


def test_compare_to_benchmarks_skips_missing_metric(tmp_path: Path):
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

    df = pd.DataFrame({"date": ["2026-01-01"], "activity_level": [50]})
    out = compare_to_benchmarks(df, spec_path=spec, group="adult", metrics=("steps",))
    assert len(out) == 1
    assert out[0].user_mean is None
    assert out[0].approx_percentile is None

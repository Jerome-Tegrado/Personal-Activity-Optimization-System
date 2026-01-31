from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd


def test_paos_run_report_supports_benchmarks_spec(tmp_path: Path):
    bench = tmp_path / "bench.csv"
    bench.write_text(
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
            "steps": [4000, 6000, 7000, 8000, 9000, 9500, 12000],
            "activity_level": [40, 42, 44, 60, 62, 64, 66],
            "energy_focus": [2, 2, 3, 4, 4, 5, 5],
            "did_exercise": ["Yes"] * 7,
            "lifestyle_status": ["Lightly Active"] * 7,
        }
    )

    processed_csv = tmp_path / "daily_log_enriched.csv"
    df.to_csv(processed_csv, index=False)

    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "scripts/paos_run.py",
        "report",
        "--processed",
        str(processed_csv),
        "--out",
        str(out_dir),
        "--benchmarks-spec",
        str(bench),
        "--benchmark-group",
        "adult",
        "--benchmark-metrics",
        "steps",
        "--no-figures",
    ]

    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert r.returncode == 0, f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"

    summary = out_dir / "summary.md"
    assert summary.exists()
    text = summary.read_text(encoding="utf-8")

    assert "## Benchmarks" in text
    assert "Steps" in text

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd


def test_paos_run_report_supports_experiments_spec(tmp_path: Path):
    """
    End-to-end smoke test:
    - writes a small enriched CSV
    - writes an experiments spec CSV
    - runs: python scripts/paos_run.py report --processed ... --out ... --experiments-spec ...
    - asserts summary.md contains the Experiments section
    """
    # --- Arrange: experiment spec (control then treatment) ---
    spec_path = tmp_path / "experiments.csv"
    spec_path.write_text(
        "\n".join(
            [
                "experiment,start_date,end_date,phase,label",
                "lunch-walk,2026-01-01,2026-01-03,control,baseline",
                "lunch-walk,2026-01-04,2026-01-07,treatment,walk-after-lunch",
            ]
        ),
        encoding="utf-8",
    )

    # --- Arrange: enriched CSV input for report stage ---
    # Needs at least: date, activity_level, energy_focus, did_exercise, lifestyle_status
    df = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=7, freq="D").astype(str),
            "steps": [7000, 7200, 7400, 9000, 9200, 9400, 9600],
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

    # --- Act ---
    cmd = [
        sys.executable,
        "scripts/paos_run.py",
        "report",
        "--processed",
        str(processed_csv),
        "--out",
        str(out_dir),
        "--experiments-spec",
        str(spec_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert result.returncode == 0, f"paos_run.py failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    # --- Assert ---
    summary_path = out_dir / "summary.md"
    assert summary_path.exists()

    text = summary_path.read_text(encoding="utf-8")
    assert "## Experiments" in text
    assert "### lunch-walk" in text

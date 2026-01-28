from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def test_dump_raw_requires_sheets() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/paos_run.py",
            "all",
            "--input-type",
            "csv",
            "--dump-raw",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "--dump-raw is only supported with --input-type sheets" in combined


def test_raw_out_creates_snapshot_for_sheets() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/paos_run.py",
            "all",
            "--input-type",
            "sheets",
            "--dump-raw",
            "--raw-out",
            "data/processed/custom_raw.csv",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    combined = (result.stdout + result.stderr).lower()
    assert "paos run complete" in combined
    assert "data/processed/custom_raw.csv" in combined

    assert Path("data/processed/custom_raw.csv").exists()

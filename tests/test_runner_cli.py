from __future__ import annotations

import os
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
    raw_path = Path("data/processed/custom_raw.csv")
    if raw_path.exists():
        raw_path.unlink()

    helpers_dir = Path("tests/helpers").resolve()
    repo_root = Path(".").resolve()

    env = dict(os.environ)
    # Ensure the subprocess auto-imports tests/helpers/sitecustomize.py
    # Keep repo root on PYTHONPATH so imports like "paos" resolve.
    existing = env.get("PYTHONPATH", "")
    parts = [str(helpers_dir), str(repo_root)]
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)


    result = subprocess.run(
        [
            sys.executable,
            "scripts/paos_run.py",
            "all",
            "--input-type",
            "sheets",
            "--dump-raw",
            "--raw-out",
            str(raw_path),
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0

    combined = (result.stdout + result.stderr).lower()
    assert "paos run complete" in combined
    assert str(raw_path).lower() in combined
    assert raw_path.exists()

    # cleanup
    raw_path.unlink()

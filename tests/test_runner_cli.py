from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def _subprocess_env_with_sitecustomize() -> dict[str, str]:
    helpers_dir = Path("tests/helpers").resolve()
    repo_root = Path(".").resolve()

    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    parts = [str(helpers_dir), str(repo_root)]
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


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


def test_raw_out_creates_snapshot_for_sheets(tmp_path: Path) -> None:
    raw_path = tmp_path / "custom_raw.csv"
    out_dir = tmp_path / "reports"
    processed_path = tmp_path / "daily_log_enriched.csv"

    env = _subprocess_env_with_sitecustomize()

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
            "--out",
            str(out_dir),
            "--processed",
            str(processed_path),
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
    assert processed_path.exists()
    assert (out_dir / "summary.md").exists()

    # Verify the snapshot looks like a raw Sheets/Forms export (pre-clean headers)
    raw_text = raw_path.read_text(encoding="utf-8")
    assert "Timestamp" in raw_text
    assert "Did you exercise today?" in raw_text
    assert "energy_focus" not in raw_text


def test_raw_out_requires_dump_raw(tmp_path: Path) -> None:
    raw_path = tmp_path / "custom_raw.csv"

    env = _subprocess_env_with_sitecustomize()

    result = subprocess.run(
        [
            sys.executable,
            "scripts/paos_run.py",
            "all",
            "--input-type",
            "sheets",
            "--raw-out",
            str(raw_path),  # set without --dump-raw
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "--raw-out requires --dump-raw" in combined


def test_csv_run_writes_outputs(tmp_path: Path) -> None:
    input_csv = tmp_path / "daily_log.csv"
    input_csv.write_text(
        "date,steps,energy_focus,did_exercise,notes\n"
        "2026-01-01,8000,4,No,\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "reports"
    processed_path = tmp_path / "daily_log_enriched.csv"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/paos_run.py",
            "all",
            "--input-type",
            "csv",
            "--input",
            str(input_csv),
            "--out",
            str(out_dir),
            "--processed",
            str(processed_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    combined = (result.stdout + result.stderr).lower()
    assert "paos run complete" in combined

    assert processed_path.exists()
    assert (out_dir / "summary.md").exists()


def test_csv_missing_input_errors(tmp_path: Path) -> None:
    missing_csv = tmp_path / "missing.csv"
    out_dir = tmp_path / "reports"
    processed_path = tmp_path / "daily_log_enriched.csv"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/paos_run.py",
            "all",
            "--input-type",
            "csv",
            "--input",
            str(missing_csv),
            "--out",
            str(out_dir),
            "--processed",
            str(processed_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "input csv not found" in combined

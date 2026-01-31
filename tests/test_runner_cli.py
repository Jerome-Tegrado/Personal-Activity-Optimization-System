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
            "--sheet-id",
            "TEST_SHEET_ID",
            "--sheet-range",
            "Form Responses 1!A1:J",
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


def test_ingest_stage_writes_ingested_csv(tmp_path: Path) -> None:
    input_csv = tmp_path / "daily_log.csv"
    input_csv.write_text(
        "date,steps,energy_focus,did_exercise,notes\n"
        "2026-01-01,8000,4,No,\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "reports"
    processed_path = tmp_path / "daily_log_ingested.csv"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/paos_run.py",
            "ingest",
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
    assert "paos ingest complete" in combined

    assert processed_path.exists()
    # Ingest stage should NOT generate reports
    assert not (out_dir / "summary.md").exists()


def test_transform_stage_writes_processed_csv(tmp_path: Path) -> None:
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
            "transform",
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
    assert "paos transform complete" in combined

    assert processed_path.exists()
    # Transform stage should NOT generate reports
    assert not (out_dir / "summary.md").exists()


def test_report_stage_missing_processed_csv_errors(tmp_path: Path) -> None:
    missing = tmp_path / "missing_enriched.csv"
    out_dir = tmp_path / "reports"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/paos_run.py",
            "report",
            "--processed",
            str(missing),
            "--out",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "processed csv not found for report stage" in combined


def test_report_stage_generates_summary_from_enriched_csv(tmp_path: Path) -> None:
    # 1) Create a tiny input CSV
    input_csv = tmp_path / "daily_log.csv"
    input_csv.write_text(
        "date,steps,energy_focus,did_exercise,notes\n"
        "2026-01-01,8000,4,No,\n",
        encoding="utf-8",
    )

    # 2) Run transform to produce an enriched CSV
    enriched_path = tmp_path / "daily_log_enriched.csv"
    transform_out_dir = tmp_path / "transform_reports"

    transform_result = subprocess.run(
        [
            sys.executable,
            "scripts/paos_run.py",
            "transform",
            "--input-type",
            "csv",
            "--input",
            str(input_csv),
            "--processed",
            str(enriched_path),
            "--out",
            str(transform_out_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert transform_result.returncode == 0
    assert enriched_path.exists()

    # 3) Run report using the enriched CSV (no ingestion, no scoring)
    report_out_dir = tmp_path / "report_outputs"
    report_result = subprocess.run(
        [
            sys.executable,
            "scripts/paos_run.py",
            "report",
            "--processed",
            str(enriched_path),
            "--out",
            str(report_out_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert report_result.returncode == 0
    combined = (report_result.stdout + report_result.stderr).lower()
    assert "paos report complete" in combined

    # Report outputs should exist
    assert (report_out_dir / "summary.md").exists()


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


def test_runner_version_flag() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/paos_run.py", "--version"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    combined = (result.stdout + result.stderr).strip().lower()
    assert "paos-run" in combined
    assert "unknown" not in combined

def test_report_stage_can_include_experiments_when_flag_provided(tmp_path: Path) -> None:
    # Create an enriched CSV that includes the columns used by:
    # - summary (date/activity_level/energy_focus/did_exercise/lifestyle_status)
    # - export_figures (requires steps in your current viz pipeline)
    enriched_path = tmp_path / "daily_log_enriched.csv"
    enriched_path.write_text(
        "date,steps,activity_level,energy_focus,did_exercise,lifestyle_status\n"
        "2026-01-14,8000,40,2,Yes,Sedentary\n"
        "2026-01-15,8500,45,3,Yes,Sedentary\n"
        "2026-01-16,10000,60,4,Yes,Sedentary\n"
        "2026-01-17,11000,65,5,Yes,Sedentary\n",
        encoding="utf-8",
    )

    spec_path = tmp_path / "experiments.csv"
    spec_path.write_text(
        "\n".join(
            [
                "experiment,start_date,end_date,phase,label",
                "e,2026-01-14,2026-01-15,control,baseline",
                "e,2026-01-16,2026-01-17,treatment,test",
            ]
        ),
        encoding="utf-8",
    )

    out_dir = tmp_path / "reports"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/paos_run.py",
            "report",
            "--processed",
            str(enriched_path),
            "--out",
            str(out_dir),
            "--experiments-spec",
            str(spec_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    summary = (out_dir / "summary.md").read_text(encoding="utf-8")
    assert "## Experiments" in summary
    assert "### e" in summary


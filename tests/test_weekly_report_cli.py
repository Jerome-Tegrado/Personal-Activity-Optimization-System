from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_weekly_report_script_csv_smoke(tmp_path: Path) -> None:
    # Minimal CSV with dates that match previous week when --today=2026-01-20
    # Previous Mon–Sun = 2026-01-13..2026-01-19
    input_csv = tmp_path / "daily_log.csv"
    input_csv.write_text(
        "date,steps,energy_focus,did_exercise,exercise_type,exercise_minutes,heart_rate_zone,notes\n"
        "2026-01-13,8200,4,Yes,cardio,30,moderate,run\n"
        "2026-01-14,6500,3,No,,,,rest\n"
        "2026-01-15,10500,5,Yes,strength,45,intense,gym\n"
        "2026-01-19,11500,4,Yes,cardio,40,moderate,walk\n",
        encoding="utf-8",
    )

    out_root = tmp_path / "out"
    processed_root = tmp_path / "processed"

    cmd = [
        sys.executable,
        "scripts/paos_weekly_report.py",
        "--quiet",
        "--input-type",
        "csv",
        "--input",
        str(input_csv),
        "--today",
        "2026-01-20",
        "--out-root",
        str(out_root),
        "--processed-root",
        str(processed_root),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"

    # Script uses ISO week folder naming (YYYY-Www)
    week_dir = out_root / "2026-W04"
    assert week_dir.exists()

    enriched_csv = processed_root / "2026-W04" / "daily_log_enriched.csv"
    assert enriched_csv.exists()


def test_weekly_report_script_csv_includes_experiments_when_spec_provided(tmp_path: Path) -> None:
    input_csv = tmp_path / "daily_log.csv"
    input_csv.write_text(
        "date,steps,energy_focus,did_exercise,notes\n"
        "2026-01-14,8000,3,Yes,\n"
        "2026-01-15,9000,4,Yes,\n"
        "2026-01-16,9500,4,Yes,\n"
        "2026-01-17,10000,5,Yes,\n"
        "2026-01-18,10500,5,Yes,\n"
        "2026-01-19,11000,4,Yes,\n"
        "2026-01-20,11500,4,Yes,\n",
        encoding="utf-8",
    )

    # Create a spec that covers these days with both control and treatment windows
    spec_csv = tmp_path / "experiments.csv"
    spec_csv.write_text(
        "\n".join(
            [
                "experiment,start_date,end_date,phase,label",
                "lunch-walk,2026-01-01,2026-01-15,control,baseline",
                "lunch-walk,2026-01-16,2026-01-31,treatment,walk-after-lunch",
            ]
        ),
        encoding="utf-8",
    )

    out_root = tmp_path / "out"
    processed_root = tmp_path / "processed"

    cmd = [
        sys.executable,
        "scripts/paos_weekly_report.py",
        "--quiet",
        "--input-type",
        "csv",
        "--input",
        str(input_csv),
        "--today",
        "2026-01-20",
        "--out-root",
        str(out_root),
        "--processed-root",
        str(processed_root),
        "--experiments-spec",
        str(spec_csv),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"

    week_dir = out_root / "2026-W04"
    summary_path = week_dir / "summary.md"
    assert summary_path.exists()

    text = summary_path.read_text(encoding="utf-8")
    assert "## Experiments" in text
    assert "lunch-walk" in text

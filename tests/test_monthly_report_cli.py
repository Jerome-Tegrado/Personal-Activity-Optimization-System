from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_monthly_report_script_csv_smoke(tmp_path: Path) -> None:
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
        "scripts/paos_monthly_report.py",
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

    month_dir = out_root / "2026-01"
    assert month_dir.exists()

    enriched_csv = processed_root / "2026-01" / "daily_log_enriched.csv"
    assert enriched_csv.exists()

    summary_md = month_dir / "summary.md"
    assert summary_md.exists()

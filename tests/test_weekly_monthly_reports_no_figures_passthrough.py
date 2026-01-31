from __future__ import annotations

import subprocess
import sys


def test_weekly_report_accepts_no_figures_flag():
    cmd = [
        sys.executable,
        "scripts/paos_weekly_report.py",
        "--input-type",
        "csv",
        "--no-figures",
        # intentionally omit --input to force a known error path
        "--quiet",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)

    # Should fail because --input is required for csv, but should NOT be an argparse "unrecognized arguments" failure
    combined = (r.stdout or "") + (r.stderr or "")
    assert "unrecognized arguments: --no-figures" not in combined.lower()


def test_monthly_report_accepts_no_figures_flag():
    cmd = [
        sys.executable,
        "scripts/paos_monthly_report.py",
        "--input-type",
        "csv",
        "--no-figures",
        # intentionally omit --input to force a known error path
        "--quiet",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)

    combined = (r.stdout or "") + (r.stderr or "")
    assert "unrecognized arguments: --no-figures" not in combined.lower()

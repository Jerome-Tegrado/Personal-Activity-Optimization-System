from __future__ import annotations

import subprocess
import sys


def test_dump_raw_requires_sheets() -> None:
    # Run the CLI in a subprocess to test argument validation behavior
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

    # argparse/SystemExit should exit non-zero
    assert result.returncode != 0

    # message comes through stdout or stderr depending on how SystemExit is handled
    combined = (result.stdout + result.stderr).lower()
    assert "--dump-raw is only supported with --input-type sheets" in combined

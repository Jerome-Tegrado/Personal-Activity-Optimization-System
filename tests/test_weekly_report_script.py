from __future__ import annotations

from datetime import date
from pathlib import Path
import importlib.util
import sys


def _import_weekly_report_module() -> object:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "paos_weekly_report.py"

    module_name = "paos_weekly_report"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not create import spec for paos_weekly_report.py")

    module = importlib.util.module_from_spec(spec)

    # IMPORTANT: dataclasses (py3.14+) expect the defining module to exist in sys.modules
    # while the @dataclass decorator runs.
    sys.modules[module_name] = module

    spec.loader.exec_module(module)
    return module


wr = _import_weekly_report_module()


def test_week_paths_uses_iso_week_and_creates_paths(tmp_path: Path) -> None:
    out_root = tmp_path / "out"
    processed_root = tmp_path / "processed"

    paths = wr._week_paths(out_root, processed_root, date(2026, 1, 20))

    assert paths.out_dir.exists()
    assert paths.processed_csv.parent.exists()
    assert paths.out_dir.name.startswith("2026-W")


def test_build_cmd_csv_includes_input_out_and_processed(tmp_path: Path) -> None:
    out_root = tmp_path / "out"
    processed_root = tmp_path / "processed"
    paths = wr._week_paths(out_root, processed_root, date(2026, 1, 20))

    class Args:
        input_type = "csv"
        input = tmp_path / "in.csv"
        sheet_id = ""
        sheet_range = ""
        dump_raw = False
        raw_out = None
        experiments_spec = None

    cmd = wr._build_paos_run_cmd(Args, paths)

    assert cmd[1:3] == ["scripts/paos_run.py", "all"]
    assert "--input-type" in cmd and "csv" in cmd
    assert "--input" in cmd and str(Args.input) in cmd
    assert "--out" in cmd and str(paths.out_dir) in cmd
    assert "--processed" in cmd and str(paths.processed_csv) in cmd


def test_build_cmd_csv_includes_experiments_spec_when_provided(tmp_path: Path) -> None:
    out_root = tmp_path / "out"
    processed_root = tmp_path / "processed"
    paths = wr._week_paths(out_root, processed_root, date(2026, 1, 20))

    class Args:
        input_type = "csv"
        input = tmp_path / "in.csv"
        sheet_id = ""
        sheet_range = ""
        dump_raw = False
        raw_out = None
        experiments_spec = tmp_path / "experiments.csv"

    cmd = wr._build_paos_run_cmd(Args, paths)

    assert "--experiments-spec" in cmd
    assert str(Args.experiments_spec) in cmd


def test_build_cmd_sheets_includes_optional_sheet_args(tmp_path: Path) -> None:
    out_root = tmp_path / "out"
    processed_root = tmp_path / "processed"
    paths = wr._week_paths(out_root, processed_root, date(2026, 1, 20))

    class Args:
        input_type = "sheets"
        input = None
        sheet_id = "abc123"
        sheet_range = "Form Responses 1!A1:J"
        dump_raw = True
        raw_out = tmp_path / "raw.csv"
        experiments_spec = None

    cmd = wr._build_paos_run_cmd(Args, paths)

    assert "--input-type" in cmd and "sheets" in cmd
    assert "--sheet-id" in cmd and "abc123" in cmd
    assert "--sheet-range" in cmd and "Form Responses 1!A1:J" in cmd
    assert "--dump-raw" in cmd
    assert "--raw-out" in cmd and str(Args.raw_out) in cmd

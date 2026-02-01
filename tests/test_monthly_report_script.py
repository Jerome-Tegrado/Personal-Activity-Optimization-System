from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path


def _import_monthly_report_module() -> object:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "paos_monthly_report.py"

    module_name = "paos_monthly_report"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not create import spec for paos_monthly_report.py")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module  # needed for dataclasses on py3.14+
    spec.loader.exec_module(module)
    return module


mr = _import_monthly_report_module()


def test_month_paths_creates_month_folder_and_processed_csv(tmp_path: Path) -> None:
    out_root = tmp_path / "out"
    processed_root = tmp_path / "processed"

    paths = mr._month_paths(out_root, processed_root, date(2026, 1, 20))

    assert paths.out_dir.exists()
    assert paths.processed_csv.parent.exists()
    assert paths.month_label == "2026-01"
    assert paths.out_dir.name == "2026-01"


def test_build_cmd_csv_includes_input_out_and_processed(tmp_path: Path) -> None:
    out_root = tmp_path / "out"
    processed_root = tmp_path / "processed"
    paths = mr._month_paths(out_root, processed_root, date(2026, 1, 20))

    class Args:
        input_type = "csv"
        input = tmp_path / "in.csv"
        sheet_id = ""
        sheet_range = ""
        dump_raw = False
        raw_out = None

    cmd = mr._build_paos_run_cmd(Args, paths)

    assert cmd[1:3] == ["scripts/paos_run.py", "all"]
    assert "--input-type" in cmd and "csv" in cmd
    assert "--input" in cmd and str(Args.input) in cmd
    assert "--out" in cmd and str(paths.out_dir) in cmd
    assert "--processed" in cmd and str(paths.processed_csv) in cmd


def test_build_cmd_includes_experiments_spec_when_provided(tmp_path: Path) -> None:
    out_root = tmp_path / "out"
    processed_root = tmp_path / "processed"
    paths = mr._month_paths(out_root, processed_root, date(2026, 1, 20))

    spec_path = tmp_path / "experiments.csv"
    spec_path.write_text(
        "\n".join(
            [
                "experiment,start_date,end_date,phase,label",
                "e,2026-01-01,2026-01-10,control,baseline",
                "e,2026-01-11,2026-01-20,treatment,test",
            ]
        ),
        encoding="utf-8",
    )

    class Args:
        input_type = "csv"
        input = tmp_path / "in.csv"
        sheet_id = ""
        sheet_range = ""
        dump_raw = False
        raw_out = None
        experiments_spec = spec_path

    cmd = mr._build_paos_run_cmd(Args, paths)

    assert "--experiments-spec" in cmd
    idx = cmd.index("--experiments-spec")
    assert cmd[idx + 1] == str(spec_path)

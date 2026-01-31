from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


@dataclass(frozen=True)
class WeeklyPaths:
    out_dir: Path
    processed_csv: Path


def _parse_iso_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as e:
        raise argparse.ArgumentTypeError("today must be in YYYY-MM-DD format") from e


def _week_paths(out_root: Path, processed_root: Path, today: date) -> WeeklyPaths:
    iso_year, iso_week, _ = today.isocalendar()
    week_label = f"{iso_year}-W{iso_week:02d}"

    out_dir = out_root / week_label
    processed_csv = processed_root / week_label / "daily_log_enriched.csv"

    out_dir.mkdir(parents=True, exist_ok=True)
    processed_csv.parent.mkdir(parents=True, exist_ok=True)

    return WeeklyPaths(out_dir=out_dir, processed_csv=processed_csv)


def _build_paos_run_cmd(args: argparse.Namespace, paths: WeeklyPaths) -> list[str]:
    cmd = [
        sys.executable,
        "scripts/paos_run.py",
        "all",
        "--input-type",
        args.input_type,
        "--out",
        str(paths.out_dir),
        "--processed",
        str(paths.processed_csv),
    ]

    if args.input_type == "csv":
        cmd += ["--input", str(args.input)]
    else:
        # sheets: allow optional args (env defaults may exist in your config)
        if args.sheet_id:
            cmd += ["--sheet-id", args.sheet_id]
        if args.sheet_range:
            cmd += ["--sheet-range", args.sheet_range]

        if args.dump_raw:
            cmd += ["--dump-raw"]
            if args.raw_out:
                cmd += ["--raw-out", str(args.raw_out)]

    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a weekly PAOS report by running the PAOS runner into a week-stamped folder."
    )

    parser.add_argument(
        "--input-type",
        choices=["csv", "sheets"],
        required=True,
        help="Input source type for ingestion.",
    )

    parser.add_argument(
        "--input",
        type=Path,
        help="Path to input CSV (required when --input-type csv).",
    )

    parser.add_argument(
        "--sheet-id",
        type=str,
        default="",
        help="Google Sheets spreadsheet id (optional if env defaults are set).",
    )

    parser.add_argument(
        "--sheet-range",
        type=str,
        default="",
        help="Google Sheets A1 range (optional if env defaults are set).",
    )

    parser.add_argument(
        "--today",
        type=_parse_iso_date,
        default=date.today(),
        help="Anchor date for week folder naming (YYYY-MM-DD). Defaults to today.",
    )

    parser.add_argument(
        "--out-root",
        type=Path,
        default=Path("reports") / "weekly",
        help="Root output folder. A YYYY-Www folder will be created inside.",
    )

    parser.add_argument(
        "--processed-root",
        type=Path,
        default=Path("data") / "processed" / "weekly",
        help="Root processed folder. A YYYY-Www folder will be created inside.",
    )

    # Optional: passthrough debug flags for Sheets
    parser.add_argument(
        "--dump-raw",
        action="store_true",
        help="(Sheets only) Dump raw Sheets snapshot before cleaning (passes through to paos_run.py).",
    )
    parser.add_argument(
        "--raw-out",
        type=Path,
        default=None,
        help="(Sheets only) Output path for raw snapshot (requires --dump-raw).",
    )

    args = parser.parse_args()

    if args.input_type == "csv" and args.input is None:
        parser.error("--input is required when --input-type csv")

    if args.input_type != "sheets" and (args.dump_raw or args.raw_out is not None):
        parser.error("--dump-raw/--raw-out are only valid with --input-type sheets")

    if args.raw_out is not None and not args.dump_raw:
        parser.error("--raw-out requires --dump-raw")

    paths = _week_paths(args.out_root, args.processed_root, args.today)
    cmd = _build_paos_run_cmd(args, paths)

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, check=False)

    if result.returncode != 0:
        print(f"Weekly report failed (exit={result.returncode})")
        return result.returncode

    print(f"Weekly report complete ✅")
    print(f"- Out dir: {paths.out_dir}")
    print(f"- Enriched CSV: {paths.processed_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

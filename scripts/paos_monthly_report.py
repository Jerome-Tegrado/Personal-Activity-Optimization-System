from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


@dataclass(frozen=True)
class MonthlyPaths:
    out_dir: Path
    processed_csv: Path
    month_label: str


def _parse_iso_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as e:
        raise argparse.ArgumentTypeError("today must be in YYYY-MM-DD format") from e


def _month_label_for(today: date) -> str:
    return f"{today.year:04d}-{today.month:02d}"


def _month_paths(out_root: Path, processed_root: Path, today: date) -> MonthlyPaths:
    month_label = _month_label_for(today)

    out_dir = out_root / month_label
    processed_csv = processed_root / month_label / "daily_log_enriched.csv"

    out_dir.mkdir(parents=True, exist_ok=True)
    processed_csv.parent.mkdir(parents=True, exist_ok=True)

    return MonthlyPaths(out_dir=out_dir, processed_csv=processed_csv, month_label=month_label)


def _build_paos_transform_cmd(args: argparse.Namespace, paths: MonthlyPaths) -> list[str]:
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
        if args.sheet_id:
            cmd += ["--sheet-id", args.sheet_id]
        if args.sheet_range:
            cmd += ["--sheet-range", args.sheet_range]

        if args.dump_raw:
            cmd += ["--dump-raw"]
            if args.raw_out:
                cmd += ["--raw-out", str(args.raw_out)]

    # experiments passthrough
    if getattr(args, "experiments_spec", None):
        cmd += ["--experiments-spec", str(args.experiments_spec)]

    # ✅ benchmarks passthrough
    if getattr(args, "benchmarks_spec", None):
        cmd += ["--benchmarks-spec", str(args.benchmarks_spec)]
    if getattr(args, "benchmark_group", None):
        cmd += ["--benchmark-group", str(args.benchmark_group)]
    if getattr(args, "benchmark_metrics", None):
        cmd += ["--benchmark-metrics", str(args.benchmark_metrics)]

    # no-figures passthrough
    if getattr(args, "no_figures", False):
        cmd += ["--no-figures"]

    return cmd


def _build_paos_run_cmd(args: argparse.Namespace, paths: MonthlyPaths) -> list[str]:
    return _build_paos_transform_cmd(args, paths)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a monthly PAOS report by running the PAOS runner into a month-stamped folder."
        )
    )

    parser.add_argument("--input-type", choices=["csv", "sheets"], required=True)
    parser.add_argument("--input", type=Path, help="CSV input path (required for csv).")

    parser.add_argument("--sheet-id", type=str, default="")
    parser.add_argument("--sheet-range", type=str, default="")

    parser.add_argument("--today", type=_parse_iso_date, default=date.today())

    parser.add_argument("--out-root", type=Path, default=Path("reports") / "monthly")
    parser.add_argument(
        "--processed-root", type=Path, default=Path("data") / "processed" / "monthly"
    )

    parser.add_argument("--dump-raw", action="store_true")
    parser.add_argument("--raw-out", type=Path, default=None)

    parser.add_argument("--experiments-spec", type=Path, default=None)

    # ✅ Benchmarks (opt-in)
    parser.add_argument(
        "--benchmarks-spec",
        type=Path,
        default=None,
        help="Path to benchmarks CSV spec. If omitted, no Benchmarks section is included.",
    )
    parser.add_argument(
        "--benchmark-group",
        type=str,
        default="adult",
        help='Benchmark group name (must match "group" in the benchmarks CSV).',
    )
    parser.add_argument(
        "--benchmark-metrics",
        type=str,
        default="steps,activity_level",
        help='Comma-separated metrics to benchmark (e.g. "steps,activity_level").',
    )

    parser.add_argument("--no-figures", action="store_true")
    parser.add_argument("--quiet", action="store_true")

    args = parser.parse_args()

    if args.input_type == "csv" and args.input is None:
        parser.error("--input is required when --input-type csv")

    if args.input_type != "sheets" and (args.dump_raw or args.raw_out is not None):
        parser.error("--dump-raw/--raw-out are only valid with --input-type sheets")

    if args.raw_out is not None and not args.dump_raw:
        parser.error("--raw-out requires --dump-raw")

    paths = _month_paths(args.out_root, args.processed_root, args.today)
    cmd = _build_paos_transform_cmd(args, paths)

    if args.quiet:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    else:
        print("Running:", " ".join(cmd))
        result = subprocess.run(cmd, check=False)

    if result.returncode != 0:
        if args.quiet:
            sys.stderr.write(result.stdout or "")
            sys.stderr.write(result.stderr or "")
        print(f"Monthly report failed (exit={result.returncode})")
        return result.returncode

    # Write monthly summary
    try:
        import pandas as pd

        from paos.analysis.summary import write_monthly_summary
    except Exception as e:
        print(f"Monthly report complete (summary skipped: {e})")
        return 0

    if paths.processed_csv.exists():
        df_enriched = pd.read_csv(paths.processed_csv)
        summary_path = paths.out_dir / "summary.md"
        write_monthly_summary(
            df_enriched,
            summary_path,
            month=paths.month_label,
            experiments_spec=args.experiments_spec,
            benchmarks_spec=args.benchmarks_spec,
            benchmark_group=args.benchmark_group,
            benchmark_metrics=tuple(
                x.strip() for x in args.benchmark_metrics.split(",") if x.strip()
            ),
        )

    if not args.quiet:
        print("Monthly report complete")
        print(f"- Month:   {paths.month_label}")
        print(f"- Out dir: {paths.out_dir}")
        print(f"- Enriched CSV: {paths.processed_csv}")
        if args.no_figures:
            print("- Figures: skipped (--no-figures)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

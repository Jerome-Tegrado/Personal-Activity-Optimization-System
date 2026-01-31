# scripts/paos_run.py
from __future__ import annotations

import argparse
from pathlib import Path

import paos
from paos.viz.export import export_figures


def _pick_fn(module, candidates: tuple[str, ...]):
    for name in candidates:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    raise RuntimeError(
        f"Could not find a function in {module.__name__} with any of these names: {candidates}"
    )


def _parse_csv_list(value: str) -> tuple[str, ...]:
    items = [x.strip() for x in (value or "").split(",")]
    items = [x for x in items if x]
    return tuple(items)


def main() -> None:
    parser = argparse.ArgumentParser(description="PAOS pipeline runner")

    parser.add_argument(
        "--version",
        action="version",
        version=f"paos-run {getattr(paos, '__version__', 'unknown')}",
    )

    parser.add_argument(
        "stage",
        choices=["all", "ingest", "transform", "report", "train-model", "predict-energy"],
        help="Pipeline stage to run",
    )

    # Input selection
    parser.add_argument(
        "--input-type",
        choices=["csv", "sheets"],
        default="csv",
        help="Input source type",
    )

    # CSV inputs (default path kept)
    parser.add_argument("--input", default="data/sample/daily_log.csv", help="Input CSV path")

    # Sheets inputs (optional; can fallback to config/env)
    parser.add_argument("--sheet-id", default=None, help="Google Sheets spreadsheet ID")
    parser.add_argument(
        "--sheet-range",
        default=None,
        help='Sheets A1 range, e.g. "Form Responses 1!A1:J"',
    )

    # Sheets debug option (raw snapshot)
    parser.add_argument(
        "--dump-raw",
        action="store_true",
        help="Dump raw Sheets pull (Sheets input only).",
    )
    parser.add_argument(
        "--raw-out",
        default="data/processed/sheets_raw.csv",
        help="Path for raw Sheets snapshot (only used with --input-type sheets --dump-raw).",
    )

    parser.add_argument(
        "--processed",
        default="data/processed/daily_log_enriched.csv",
        help="Output enriched CSV (also used as input for report/train-model/predict-energy).",
    )
    parser.add_argument(
        "--out",
        default="reports",
        help="Output folder for reports (summary + figures)",
    )

    # Experiments (opt-in)
    parser.add_argument(
        "--experiments-spec",
        default=None,
        help="Path to experiments CSV spec. If omitted, no Experiments section is included.",
    )

    # ✅ Benchmarks (opt-in)
    parser.add_argument(
        "--benchmarks-spec",
        default=None,
        help="Path to benchmarks CSV spec. If omitted, no Benchmarks section is included.",
    )
    parser.add_argument(
        "--benchmark-group",
        default="adult",
        help='Benchmark group name to use (must match "group" in the benchmarks CSV).',
    )
    parser.add_argument(
        "--benchmark-metrics",
        default="steps,activity_level",
        help='Comma-separated metrics to benchmark (e.g. "steps,activity_level").',
    )

    # Figures
    parser.add_argument(
        "--no-figures",
        action="store_true",
        help="Skip figure generation (faster + more reliable in CI).",
    )

    # v3 Machine Learning options (Section 1)
    parser.add_argument(
        "--model-type",
        default="ridge",
        choices=["baseline", "ridge", "rf"],
        help="Energy model type to train/evaluate",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Test split size for evaluation (time-based)",
    )
    parser.add_argument(
        "--model-path",
        default="models/energy_model.pkl",
        help="Path to save/load the trained energy model",
    )
    parser.add_argument(
        "--eval-out",
        default=None,
        help="Optional path to write evaluation JSON (default: <out>/model/energy_eval.json)",
    )
    parser.add_argument(
        "--pred-out",
        default="data/processed/daily_log_enriched_with_preds.csv",
        help="Output CSV path for enriched data with energy predictions",
    )

    args = parser.parse_args()

    # Guard: dump-raw is only valid for Sheets input
    if args.dump_raw and args.input_type != "sheets":
        raise SystemExit("--dump-raw is only supported with --input-type sheets")

    # Guard: raw-out should only be set when dump-raw is enabled
    if (
        args.input_type == "sheets"
        and not args.dump_raw
        and args.raw_out != "data/processed/sheets_raw.csv"
    ):
        raise SystemExit("--raw-out requires --dump-raw")

    out_path = Path(args.processed)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    import paos.transform.scoring as scoring
    from paos.analysis.summary import write_weekly_summary
    from paos.ingest import load_daily_log

    enrich_fn = _pick_fn(scoring, ("enrich_daily_log", "enrich", "score_and_enrich", "add_scores"))
    bench_metrics = _parse_csv_list(args.benchmark_metrics)

    # ✅ report-only stage (build summary + figures from an existing enriched CSV)
    if args.stage == "report":
        import pandas as pd

        if not out_path.exists():
            raise SystemExit(f"Processed CSV not found for report stage: {out_path}")

        df_enriched = pd.read_csv(out_path)

        summary_path = out_dir / "summary.md"
        write_weekly_summary(
            df_enriched,
            summary_path,
            experiments_spec=args.experiments_spec,
            benchmarks_spec=args.benchmarks_spec,
            benchmark_group=args.benchmark_group,
            benchmark_metrics=bench_metrics,
        )

        if not args.no_figures:
            export_figures(df_enriched, out_dir)

        print("PAOS report complete")
        print(f"- Input:   {out_path}")
        print(f"- Out dir: {out_dir}")
        print(f"- Summary: {summary_path}")
        if args.no_figures:
            print("- Figures: skipped (--no-figures)")
        return

    # ✅ v3: train-model stage (train + eval from existing enriched CSV)
    if args.stage == "train-model":
        if not out_path.exists():
            raise SystemExit(f"Processed CSV not found for train-model stage: {out_path}")

        from paos.machine_learning.cli import train_and_evaluate_from_enriched_csv

        model_path = Path(args.model_path)
        eval_out = Path(args.eval_out) if args.eval_out else (out_dir / "model" / "energy_eval.json")

        result = train_and_evaluate_from_enriched_csv(
            enriched_csv_path=out_path,
            model_out_path=model_path,
            eval_out_path=eval_out,
            model_type=args.model_type,
            test_size=args.test_size,
        )

        print("PAOS train-model complete")
        print(f"- Input:      {out_path}")
        print(f"- Model:      {model_path}")
        print(f"- Eval JSON:  {eval_out}")
        print(f"- MAE/RMSE:   {float(result.get('mae')):.3f} / {float(result.get('rmse')):.3f}")
        print(
            f"- Baseline:   {float(result.get('baseline_mae')):.3f} / {float(result.get('baseline_rmse')):.3f}"
        )
        return

    # ✅ v3: predict-energy stage (write energy_focus_pred into a new CSV)
    if args.stage == "predict-energy":
        if not out_path.exists():
            raise SystemExit(f"Processed CSV not found for predict-energy stage: {out_path}")

        model_path = Path(args.model_path)
        if not model_path.exists():
            raise SystemExit(
                f"Model not found: {model_path}\n"
                "Run: python scripts/paos_run.py train-model --processed <enriched.csv> --model-path <path>"
            )

        from paos.machine_learning.cli import predict_energy_into_csv

        pred_out = Path(args.pred_out)

        predict_energy_into_csv(
            enriched_csv_path=out_path,
            model_path=model_path,
            out_csv_path=pred_out,
            pred_col="energy_focus_pred",
        )

        print("PAOS predict-energy complete")
        print(f"- Input:    {out_path}")
        print(f"- Model:    {model_path}")
        print(f"- Output:   {pred_out}")
        return

    # --- Ingest (unified) ---
    if args.input_type == "csv":
        input_path = Path(args.input)
        if not input_path.exists():
            raise SystemExit(f"Input CSV not found: {input_path}")

        df_raw = load_daily_log("csv", path=input_path)
        input_label = str(input_path)

    else:
        from paos.config import DEFAULT_SHEETS_ID, DEFAULT_SHEETS_RANGE

        sheet_id = (args.sheet_id or DEFAULT_SHEETS_ID).strip()
        sheet_range = (args.sheet_range or DEFAULT_SHEETS_RANGE).strip()

        if not sheet_id:
            raise SystemExit(
                "Missing Sheets spreadsheet id.\n\n"
                "Provide one of:\n"
                '  1) CLI: --sheet-id "..." \n'
                "  2) Env: set PAOS_SHEETS_ID\n\n"
                "Example:\n"
                'python scripts/paos_run.py all --input-type sheets --sheet-id "..." '
                '--sheet-range "Form Responses 1!A1:J" --out reports'
            )

        dump_raw_path = args.raw_out if args.dump_raw else None

        df_raw = load_daily_log(
            "sheets",
            spreadsheet_id=sheet_id,
            range_=sheet_range,
            dump_raw_path=dump_raw_path,
        )
        input_label = f"sheets:{sheet_id} ({sheet_range})"

    # ✅ ingest-only stage exits early after writing ingested CSV
    if args.stage == "ingest":
        df_raw.to_csv(out_path, index=False)

        print("PAOS ingest complete")
        print(f"- Input:   {input_label}")
        print(f"- Output:  {out_path}")

        if args.input_type == "sheets" and args.dump_raw:
            print(f"- Raw:     {args.raw_out}")

        return

    # --- Transform / enrich ---
    df_enriched = enrich_fn(df_raw)
    df_enriched.to_csv(out_path, index=False)

    # ✅ transform-only stage exits early after writing enriched CSV
    if args.stage == "transform":
        print("PAOS transform complete")
        print(f"- Input:   {input_label}")
        print(f"- Output:  {out_path}")
        return

    # --- Summary + figures ---
    summary_path = out_dir / "summary.md"
    write_weekly_summary(
        df_enriched,
        summary_path,
        experiments_spec=args.experiments_spec,
        benchmarks_spec=args.benchmarks_spec,
        benchmark_group=args.benchmark_group,
        benchmark_metrics=bench_metrics,
    )

    if not args.no_figures:
        export_figures(df_enriched, out_dir)

    print("PAOS run complete")
    print(f"- Input:   {input_label}")
    print(f"- Output:  {out_path}")
    print(f"- Out dir: {out_dir}")
    print(f"- Summary: {summary_path}")

    if args.no_figures:
        print("- Figures: skipped (--no-figures)")

    if args.input_type == "sheets" and args.dump_raw:
        print(f"- Raw:     {args.raw_out}")


if __name__ == "__main__":
    main()

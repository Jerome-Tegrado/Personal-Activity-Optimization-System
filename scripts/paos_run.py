# scripts/paos_run.py
from __future__ import annotations

import argparse
from pathlib import Path

from paos.viz.export import export_figures


def _pick_fn(module, candidates: tuple[str, ...]):
    for name in candidates:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    raise RuntimeError(
        f"Could not find a function in {module.__name__} with any of these names: {candidates}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="PAOS pipeline runner")
    parser.add_argument("stage", choices=["all"], help="Pipeline stage to run")

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
        help="Output enriched CSV",
    )
    parser.add_argument(
        "--out",
        default="reports",
        help="Output folder for reports (summary + figures)",
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

    # --- Ingest (unified) ---
    if args.input_type == "csv":
        input_path = Path(args.input)
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

    # --- Transform / enrich ---
    df_enriched = enrich_fn(df_raw)
    df_enriched.to_csv(out_path, index=False)

    # --- Summary + figures ---
    summary_path = out_dir / "summary.md"
    write_weekly_summary(df_enriched, summary_path)
    export_figures(df_enriched, out_dir)

    print("PAOS run complete")
    print(f"- Input:   {input_label}")
    print(f"- Output:  {out_path}")
    print(f"- Out dir: {out_dir}")
    print(f"- Summary: {summary_path}")

    if args.input_type == "sheets" and args.dump_raw:
        print(f"- Raw:     {args.raw_out}")


if __name__ == "__main__":
    main()

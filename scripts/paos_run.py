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

    # Sheets inputs (required when --input-type sheets)
    parser.add_argument("--sheet-id", default=None, help="Google Sheets spreadsheet ID")
    parser.add_argument(
        "--sheet-range",
        default="Form Responses 1!A1:J",
        help='Sheets A1 range, e.g. "Form Responses 1!A1:J"',
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

    out_path = Path(args.processed)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    import paos.transform.scoring as scoring
    from paos.analysis.summary import write_weekly_summary

    enrich_fn = _pick_fn(scoring, ("enrich_daily_log", "enrich", "score_and_enrich", "add_scores"))

    # --- Ingest ---
    if args.input_type == "csv":
        import paos.ingest.csv_ingest as csv_ingest

        ingest_fn = _pick_fn(
            csv_ingest, ("ingest_csv", "read_daily_log_csv", "load_daily_log_csv", "read_csv")
        )

        input_path = Path(args.input)
        df_raw = ingest_fn(input_path)

        input_label = str(input_path)

    else:
        if not args.sheet_id:
            raise SystemExit(
                "Missing --sheet-id. Example:\n"
                'python scripts/paos_run.py all --input-type sheets --sheet-id "..." '
                '--sheet-range "Form Responses 1!A1:J" --out reports'
            )

        from paos.ingest.sheets_ingest import SheetsConfig, read_daily_log_from_sheets

        cfg = SheetsConfig(
            spreadsheet_id=args.sheet_id,
            range_=args.sheet_range,
        )
        df_raw = read_daily_log_from_sheets(cfg)

        input_label = f"sheets:{args.sheet_id} ({args.sheet_range})"

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


if __name__ == "__main__":
    main()

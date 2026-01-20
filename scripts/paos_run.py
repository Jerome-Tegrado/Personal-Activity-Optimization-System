from __future__ import annotations

import argparse
from pathlib import Path


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
    parser.add_argument("--input", default="data/sample/daily_log.csv", help="Input CSV path")
    parser.add_argument("--processed", default="data/processed/daily_log_enriched.csv", help="Output enriched CSV")
    args = parser.parse_args()

    input_path = Path(args.input)
    out_path = Path(args.processed)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    import paos.ingest.csv_ingest as csv_ingest
    import paos.transform.scoring as scoring

    ingest_fn = _pick_fn(csv_ingest, ("ingest_csv", "read_daily_log_csv", "load_daily_log_csv", "read_csv"))
    enrich_fn = _pick_fn(scoring, ("enrich_daily_log", "enrich", "score_and_enrich", "add_scores"))

    df_raw = ingest_fn(input_path)
    df_enriched = enrich_fn(df_raw)

    df_enriched.to_csv(out_path, index=False)

    print("PAOS run complete")
    print(f"- Input:  {input_path}")
    print(f"- Output: {out_path}")


if __name__ == "__main__":
    main()

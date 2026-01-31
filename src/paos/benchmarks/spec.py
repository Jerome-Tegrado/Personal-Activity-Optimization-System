from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import pandas as pd

from .types import BenchmarkSpecRow


_REQUIRED_COLS = ["metric", "group", "unit", "p25", "p50", "p75", "p90"]


def load_benchmark_spec(path: str | Path) -> list[BenchmarkSpecRow]:
    """
    Load a benchmark spec CSV.

    Required columns:
      metric, group, unit, p25, p50, p75, p90

    Optional:
      source
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Benchmark spec not found: {p}")

    df = pd.read_csv(p)

    missing = [c for c in _REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Benchmark spec missing columns: {missing}")

    if "source" not in df.columns:
        df["source"] = ""

    rows: list[BenchmarkSpecRow] = []
    for _, r in df.iterrows():
        rows.append(
            BenchmarkSpecRow(
                metric=str(r["metric"]).strip(),
                group=str(r["group"]).strip(),
                unit=str(r["unit"]).strip(),
                p25=float(pd.to_numeric(r["p25"], errors="coerce")),
                p50=float(pd.to_numeric(r["p50"], errors="coerce")),
                p75=float(pd.to_numeric(r["p75"], errors="coerce")),
                p90=float(pd.to_numeric(r["p90"], errors="coerce")),
                source=str(r.get("source", "")).strip(),
            )
        )

    return rows

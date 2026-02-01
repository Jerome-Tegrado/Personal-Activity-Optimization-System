from __future__ import annotations

from pathlib import Path

import pandas as pd

from .spec import load_benchmark_spec
from .types import BenchmarkResult, BenchmarkSpecRow


def _approx_percentile_from_cutpoints(
    value: float,
    p25: float,
    p50: float,
    p75: float,
    p90: float,
) -> float:
    """
    Piecewise-linear percentile estimate using p25/p50/p75/p90.
    Returns a number in [0, 100].

    Interpretation:
    - below p25 => 0..25
    - between p25 and p50 => 25..50
    - between p50 and p75 => 50..75
    - between p75 and p90 => 75..90
    - above p90 => 90..100 (soft-capped)
    """
    # Guard against degenerate specs
    if not (p25 <= p50 <= p75 <= p90):
        # fallback: treat as unknown distribution
        return float("nan")

    if value <= p25:
        if p25 == 0:
            return 0.0
        return max(0.0, min(25.0, 25.0 * (value / p25)))

    if value <= p50:
        if p50 == p25:
            return 37.5
        return 25.0 + 25.0 * ((value - p25) / (p50 - p25))

    if value <= p75:
        if p75 == p50:
            return 62.5
        return 50.0 + 25.0 * ((value - p50) / (p75 - p50))

    if value <= p90:
        if p90 == p75:
            return 82.5
        return 75.0 + 15.0 * ((value - p75) / (p90 - p75))

    # Above p90: approach 100 slowly; don't explode.
    # Map [p90, 2*p90] => [90, 100], clamp.
    if p90 <= 0:
        return 90.0
    pct = 90.0 + 10.0 * min(1.0, (value - p90) / p90)
    return float(max(90.0, min(100.0, pct)))


def compare_to_benchmarks(
    df: pd.DataFrame,
    spec_path: str | Path,
    *,
    group: str = "adult",
    metrics: tuple[str, ...] = ("steps",),
) -> list[BenchmarkResult]:
    """
    Compare user's aggregate metric values to benchmark distributions.

    Privacy-safe:
    - uses only aggregate stats (mean/median)
    - does not output dates or notes

    Assumes df has numeric columns for requested metrics.
    """
    if df is None or df.empty:
        return []

    rows = load_benchmark_spec(spec_path)
    by_key: dict[tuple[str, str], BenchmarkSpecRow] = {(r.metric, r.group): r for r in rows}

    results: list[BenchmarkResult] = []

    for metric in metrics:
        key = (metric, group)
        spec = by_key.get(key)
        if spec is None:
            continue

        s = pd.to_numeric(df.get(metric), errors="coerce") if metric in df.columns else None
        if s is None:
            user_mean = None
            user_median = None
            approx_pct = None
        else:
            s2 = s.dropna()
            if len(s2) == 0:
                user_mean = None
                user_median = None
                approx_pct = None
            else:
                user_mean = float(s2.mean())
                user_median = float(s2.median())
                approx = _approx_percentile_from_cutpoints(
                    user_median,
                    spec.p25,
                    spec.p50,
                    spec.p75,
                    spec.p90,
                )
                approx_pct = None if pd.isna(approx) else float(approx)

        results.append(
            BenchmarkResult(
                metric=spec.metric,
                group=spec.group,
                unit=spec.unit,
                user_mean=user_mean,
                user_median=user_median,
                approx_percentile=approx_pct,
                benchmark_p25=spec.p25,
                benchmark_p50=spec.p50,
                benchmark_p75=spec.p75,
                benchmark_p90=spec.p90,
                source=spec.source,
            )
        )

    return results

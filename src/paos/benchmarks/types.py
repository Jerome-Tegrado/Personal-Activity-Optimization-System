from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BenchmarkSpecRow:
    """
    One benchmark distribution row, typically for a metric and a group.

    Percentiles are numeric cut points for the metric distribution.
    Example: steps/day p50 = 7000, p75 = 9000, etc.
    """

    metric: str
    group: str
    unit: str
    p25: float
    p50: float
    p75: float
    p90: float
    source: str = ""


@dataclass(frozen=True)
class BenchmarkResult:
    """
    Privacy-safe benchmark comparison output.
    Contains only aggregate user stats + approximate percentile vs benchmark distribution.
    """

    metric: str
    group: str
    unit: str
    user_mean: Optional[float]
    user_median: Optional[float]
    approx_percentile: Optional[float]  # 0-100
    benchmark_p25: float
    benchmark_p50: float
    benchmark_p75: float
    benchmark_p90: float
    source: str = ""

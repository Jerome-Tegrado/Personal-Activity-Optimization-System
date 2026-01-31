# Benchmarks (public-safe)

PAOS supports optional **population benchmark comparisons** in weekly/monthly summaries.

This feature is **opt-in** and uses a **benchmark spec CSV** that contains only distribution cutpoints
(p25/p50/p75/p90). PAOS then compares your aggregate stats (mean/median) and estimates an
approximate percentile using piecewise interpolation.

## Why this is safe

- PAOS outputs only **aggregate values** (mean/median) and an **approximate percentile**
- No dates, no notes, no raw per-day rows are included in the benchmark output
- You control what benchmark file is used (local or public)

## Benchmark spec format

Required columns:

- `metric` (e.g. `steps`)
- `group` (e.g. `adult`, `18_24`, `male_18_24`)
- `unit` (e.g. `steps/day`)
- `p25`, `p50`, `p75`, `p90` (numeric cutpoints)

Optional:

- `source` (free text citation or dataset label)

Example:

```csv
metric,group,unit,p25,p50,p75,p90,source
steps,adult,steps/day,5000,7000,9000,11000,example-only


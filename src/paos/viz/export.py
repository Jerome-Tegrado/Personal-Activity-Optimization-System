from __future__ import annotations

from pathlib import Path

import pandas as pd

from paos.viz.mpl_charts import (
    save_activity_trend_png,
    save_activity_vs_energy_png,
    save_status_counts_png,
)
from paos.viz.plotly_charts import activity_trend, activity_vs_energy, status_counts


def export_figures(df: pd.DataFrame, out_dir: Path) -> dict[str, Path]:
    """
    Exports:
      - Plotly HTML to: out_dir/figures/interactive/
      - Matplotlib PNG to: out_dir/figures/static/

    Returns a dict of output paths.
    """
    out_dir = Path(out_dir)
    html_dir = out_dir / "figures" / "interactive"
    png_dir = out_dir / "figures" / "static"
    html_dir.mkdir(parents=True, exist_ok=True)
    png_dir.mkdir(parents=True, exist_ok=True)

    outputs: dict[str, Path] = {}

    # Plotly HTML
    p1 = html_dir / "activity_trend.html"
    activity_trend(df).write_html(p1)
    outputs["activity_trend_html"] = p1

    p2 = html_dir / "status_counts.html"
    status_counts(df).write_html(p2)
    outputs["status_counts_html"] = p2

    p3 = html_dir / "activity_vs_energy.html"
    activity_vs_energy(df).write_html(p3)
    outputs["activity_vs_energy_html"] = p3

    # Matplotlib PNG (backup/static)
    q1 = png_dir / "activity_trend.png"
    save_activity_trend_png(df, q1)
    outputs["activity_trend_png"] = q1

    q2 = png_dir / "status_counts.png"
    save_status_counts_png(df, q2)
    outputs["status_counts_png"] = q2

    q3 = png_dir / "activity_vs_energy.png"
    save_activity_vs_energy_png(df, q3)
    outputs["activity_vs_energy_png"] = q3

    return outputs

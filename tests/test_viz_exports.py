from pathlib import Path

import pandas as pd

from paos.viz.export import export_figures


def test_export_figures_creates_files(tmp_path: Path):
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-13", "2026-01-14"]),
            "steps": [8000, 5000],
            "energy_focus": [4, 3],
            "activity_level": [70, 25],
            "lifestyle_status": ["Active", "Sedentary"],
        }
    )

    outputs = export_figures(df, tmp_path)
    for p in outputs.values():
        assert Path(p).exists()

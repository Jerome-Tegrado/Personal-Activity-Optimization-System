from pathlib import Path

import pandas as pd

from paos.experiments.assign import assign_experiments_to_days


def test_assign_experiments_to_days_basic(tmp_path: Path):
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02", "2026-01-15", "2026-01-20"],
            "steps": [7000, 8000, 9000, 10000],
        }
    )

    spec_csv = tmp_path / "experiments.csv"
    spec_csv.write_text(
        "\n".join(
            [
                "experiment,start_date,end_date,phase,label",
                "lunch-walk,2026-01-01,2026-01-14,control,baseline",
                "lunch-walk,2026-01-15,2026-01-31,treatment,walk-after-lunch",
            ]
        ),
        encoding="utf-8",
    )

    out = assign_experiments_to_days(df, spec_csv)

    assert "experiment" in out.columns
    assert "experiment_phase" in out.columns
    assert "experiment_label" in out.columns

    # early dates = control
    assert out.loc[0, "experiment"] == "lunch-walk"
    assert out.loc[0, "experiment_phase"] == "control"

    # later dates = treatment
    assert out.loc[2, "experiment"] == "lunch-walk"
    assert out.loc[2, "experiment_phase"] == "treatment"


def test_assign_experiments_overrides_last_row_wins(tmp_path: Path):
    df = pd.DataFrame({"date": ["2026-01-10"], "steps": [8000]})

    spec_csv = tmp_path / "experiments.csv"
    spec_csv.write_text(
        "\n".join(
            [
                "experiment,start_date,end_date,phase,label",
                "test,2026-01-01,2026-01-31,control,baseline",
                "test,2026-01-10,2026-01-10,treatment,override",
            ]
        ),
        encoding="utf-8",
    )

    out = assign_experiments_to_days(df, spec_csv)

    assert out.loc[0, "experiment_phase"] == "treatment"
    assert out.loc[0, "experiment_label"] == "override"

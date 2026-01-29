import pandas as pd
import pytest

from paos.dashboard.data import (
    load_enriched_csv,
    validate_required_columns,
    coerce_date_column,
    filter_by_date_range,
)


def test_load_enriched_csv_reads_file(tmp_path):
    p = tmp_path / "enriched.csv"
    p.write_text("date,steps,activity_level\n2026-01-01,1000,10\n", encoding="utf-8")

    df = load_enriched_csv(p)
    assert list(df.columns) == ["date", "steps", "activity_level"]
    assert len(df) == 1


def test_load_enriched_csv_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_enriched_csv(tmp_path / "missing.csv")


def test_validate_required_columns_raises_on_missing():
    df = pd.DataFrame({"date": ["2026-01-01"], "steps": [1000]})
    with pytest.raises(ValueError) as e:
        validate_required_columns(df, ["date", "steps", "activity_level"])
    assert "Missing required columns" in str(e.value)


def test_coerce_date_column_parses_and_coerces_bad_values():
    df = pd.DataFrame({"date": ["2026-01-01", "not-a-date"]})
    out = coerce_date_column(df)
    assert pd.notna(out.loc[0, "date"])
    assert pd.isna(out.loc[1, "date"])


def test_filter_by_date_range_inclusive_bounds():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
            "steps": [1, 2, 3],
        }
    )

    out = filter_by_date_range(
        df,
        start=pd.Timestamp("2026-01-02"),
        end=pd.Timestamp("2026-01-03"),
    )
    assert out["steps"].tolist() == [2, 3]

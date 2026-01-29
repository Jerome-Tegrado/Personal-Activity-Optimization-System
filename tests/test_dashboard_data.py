import pandas as pd
import pytest

from paos.dashboard.data import (
    load_enriched_csv,
    validate_required_columns,
    coerce_date_column,
    filter_by_date_range,
    hr_zone_breakdown,
    HR_ZONE_ORDER,
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


def test_hr_zone_breakdown_days_stable_order_and_filters_non_exercise():
    df = pd.DataFrame(
        {
            "did_exercise": ["Yes", "No", "Yes", "Yes"],
            "heart_rate_zone": ["moderate", "", "intense", "moderate"],
            "exercise_minutes": [30, None, 45, 20],
        }
    )

    out = hr_zone_breakdown(df, metric="days")

    # Always includes all zones in the same order
    assert out["heart_rate_zone"].tolist() == HR_ZONE_ORDER

    # Only exercised rows count; the blank zone row was "No", so it shouldn't show as unknown
    values = dict(zip(out["heart_rate_zone"], out["value"]))
    assert values["moderate"] == 2
    assert values["intense"] == 1
    assert values["unknown"] == 0


def test_hr_zone_breakdown_minutes_sums_minutes_and_coerces_bad_values():
    df = pd.DataFrame(
        {
            "did_exercise": ["Yes", "Yes", "Yes"],
            "heart_rate_zone": ["light", "peak", "peak"],
            "exercise_minutes": ["15", "not-a-number", 20],
        }
    )

    out = hr_zone_breakdown(df, metric="minutes")
    values = dict(zip(out["heart_rate_zone"], out["value"]))

    assert values["light"] == 15
    assert values["peak"] == 20  # bad value -> 0, so 0 + 20


def test_hr_zone_breakdown_invalid_metric_raises():
    df = pd.DataFrame(
        {"did_exercise": ["Yes"], "heart_rate_zone": ["light"], "exercise_minutes": [10]}
    )
    with pytest.raises(ValueError):
        hr_zone_breakdown(df, metric="invalid")

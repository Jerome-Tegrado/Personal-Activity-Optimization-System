import pandas as pd

from paos.insights.redact import RedactConfig, redact_dataframe


def test_redact_drops_notes_by_default():
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02"],
            "steps": [7000, 8000],
            "notes": ["private", "more private"],
        }
    )

    out = redact_dataframe(df)
    assert "notes" not in out.columns
    assert "date" in out.columns
    assert "steps" in out.columns


def test_redact_buckets_date_to_week_and_drops_date():
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02"],
            "steps": [7000, 8000],
            "notes": ["private", "more private"],
        }
    )

    cfg = RedactConfig(bucket_dates_to_week=True)
    out = redact_dataframe(df, cfg=cfg)

    assert "notes" not in out.columns
    assert "date" not in out.columns
    assert "week" in out.columns
    assert out["week"].str.startswith("2026-W").all()


def test_redact_keep_columns_limits_output():
    df = pd.DataFrame(
        {
            "date": ["2026-01-01"],
            "steps": [7000],
            "energy_focus": [4],
            "notes": ["private"],
        }
    )

    cfg = RedactConfig(drop_notes=True, keep_columns=["date", "steps"])
    out = redact_dataframe(df, cfg=cfg)

    assert list(out.columns) == ["date", "steps"]

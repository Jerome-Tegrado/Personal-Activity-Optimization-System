import pandas as pd

from paos.machine_learning.features import build_energy_features


def _make_df(n=10):
    dates = pd.date_range("2026-01-01", periods=n, freq="D")
    # simple increasing activity
    activity = list(range(10, 10 + n))
    steps = [5000 + i * 100 for i in range(n)]
    energy = [1 + (i % 5) for i in range(n)]  # 1..5 repeating

    return pd.DataFrame(
        {
            "date": dates.astype(str),
            "steps": steps,
            "activity_level": activity,
            "energy_focus": energy,
        }
    )


def test_build_energy_features_outputs_expected_columns():
    df = _make_df(10)
    X, y, feature_names = build_energy_features(df)

    assert list(X.columns) == feature_names
    assert "day_of_week" in X.columns
    assert "is_weekend" in X.columns
    assert "activity_level_lag_1" in X.columns
    assert "activity_level_rollmean_7" in X.columns

    # Because of lag_1, first row should be dropped => n-1 rows remain
    assert len(X) == 9
    assert len(y) == 9


def test_leakage_safe_lag_and_rolling_mean_match_expected():
    df = _make_df(10)

    X, y, _ = build_energy_features(df)

    # recreate expected using same rules (sort by date, shift(1), rolling(7, min_periods=1))
    df2 = df.copy()
    df2["date"] = pd.to_datetime(df2["date"])
    df2 = df2.sort_values("date").reset_index(drop=True)

    expected_lag = df2["activity_level"].shift(1)
    expected_roll = df2["activity_level"].shift(1).rolling(window=7, min_periods=1).mean()

    # X has dropped first row due to NaN lag, so compare from index 1..end
    assert X["activity_level_lag_1"].tolist() == expected_lag.iloc[1:].tolist()
    assert X["activity_level_rollmean_7"].tolist() == expected_roll.iloc[1:].tolist()


def test_weekday_features_are_valid_ranges():
    df = _make_df(10)
    X, _, _ = build_energy_features(df)

    assert X["day_of_week"].between(0, 6).all()
    assert set(X["is_weekend"].unique()).issubset({0, 1})

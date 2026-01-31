from __future__ import annotations

import pandas as pd

from paos.transform.recommendations import recommend, recommend_series


def test_recommendation_base_sedentary() -> None:
    msg = recommend(activity_level=10, energy_focus=3)
    assert "walk" in msg.lower()


def test_recommendation_recovery_rule_appends_message() -> None:
    msg = recommend(activity_level=80, energy_focus=2)
    assert "recovery" in msg.lower()
    assert "low energy" in msg.lower()


def test_recommendation_handles_missing_energy() -> None:
    msg = recommend(activity_level=80, energy_focus=None)
    assert msg  # non-empty


def test_recommend_series_appends_downtrend_nudge_on_third_day() -> None:
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "activity_level": [80, 70, 60],
            "energy_focus": [3, 3, 3],
        }
    )
    recs = recommend_series(df)
    assert "dipped for 3 days" in recs.iloc[2].lower()
    assert "dipped for 3 days" not in recs.iloc[0].lower()
    assert "dipped for 3 days" not in recs.iloc[1].lower()


def test_recommend_series_does_not_trigger_downtrend_with_date_gaps() -> None:
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-03", "2026-01-04"],  # gap breaks consecutiveness
            "activity_level": [80, 70, 60],
            "energy_focus": [3, 3, 3],
        }
    )
    recs = recommend_series(df)
    assert "dipped for 3 days" not in recs.iloc[2].lower()


def test_recommend_series_appends_sedentary_streak_nudge() -> None:
    df = pd.DataFrame(
        {
            "date": ["2026-01-06", "2026-01-07"],  # consecutive days
            "activity_level": [20, 10],  # both sedentary
            "energy_focus": [3, 3],
        }
    )
    recs = recommend_series(df)
    assert "two sedentary days" in recs.iloc[1].lower()
    assert "two sedentary days" not in recs.iloc[0].lower()


def test_recommend_series_escalates_on_three_sedentary_days() -> None:
    df = pd.DataFrame(
        {
            "date": ["2026-01-06", "2026-01-07", "2026-01-08"],  # consecutive days
            "activity_level": [20, 15, 10],  # all sedentary
            "energy_focus": [3, 3, 3],
        }
    )
    recs = recommend_series(df)
    assert "three sedentary days" in recs.iloc[2].lower()
    assert "three sedentary days" not in recs.iloc[0].lower()
    assert "three sedentary days" not in recs.iloc[1].lower()


def test_recommend_series_weekday_dip_nudge_triggers_on_weekday_sedentary() -> None:
    # 2026-01-05 is a Monday (weekday)
    df = pd.DataFrame(
        {
            "date": ["2026-01-05"],
            "activity_level": [10],
            "energy_focus": [3],
        }
    )
    recs = recommend_series(df)
    assert "weekday dip" in recs.iloc[0].lower()


def test_recommend_series_weekend_recovery_nudge_triggers() -> None:
    # 2026-01-10 is a Saturday
    df = pd.DataFrame(
        {
            "date": ["2026-01-10"],
            "activity_level": [80],
            "energy_focus": [2],
        }
    )
    recs = recommend_series(df)
    assert "weekend recovery" in recs.iloc[0].lower()

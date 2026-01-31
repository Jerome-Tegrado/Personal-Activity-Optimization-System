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
    assert len(recs) == 3
    assert "dipped for 3 days" in recs.iloc[2].lower()
    assert "dipped for 3 days" not in recs.iloc[0].lower()
    assert "dipped for 3 days" not in recs.iloc[1].lower()


def test_recommend_series_does_not_trigger_with_date_gaps() -> None:
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-03", "2026-01-04"],  # gap between day 1 and day 2
            "activity_level": [80, 70, 60],
            "energy_focus": [3, 3, 3],
        }
    )
    recs = recommend_series(df)
    assert "dipped for 3 days" not in recs.iloc[2].lower()

import pandas as pd

from paos.insights.engine import InsightEngineConfig, generate_insights


def test_generate_insights_returns_list():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=14, freq="D").astype(str),
            "activity_level": list(range(10, 24)),
            "energy_focus": [1, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 4, 3, 2],
            "did_exercise": ["Yes", "No"] * 7,
            "notes": ["private"] * 14,
        }
    )

    insights = generate_insights(df, cfg=InsightEngineConfig(week_mode=True, min_days=7))
    assert isinstance(insights, list)
    assert len(insights) > 0

    keys = {i.key for i in insights}
    assert "weekly_activity_avg" in keys
    assert "activity_energy_corr" in keys
    assert "exercise_energy_delta" in keys


def test_generate_insights_handles_empty_df():
    insights = generate_insights(pd.DataFrame())
    assert len(insights) == 1
    assert insights[0].key == "no_data"

import pandas as pd

from paos.transform.hr_zone_infer import (
    HRZoneInferConfig,
    infer_missing_heart_rate_zone,
    infer_zone_from_avg_hr_bpm,
    infer_zone_from_time_in_zone_row,
)


def test_infer_zone_from_time_in_zone_picks_max_minutes():
    row = pd.Series(
        {
            "minutes_light": 10,
            "minutes_moderate": 25,
            "minutes_intense": 5,
            "minutes_peak": 0,
        }
    )
    assert infer_zone_from_time_in_zone_row(row) == "moderate"


def test_infer_zone_from_time_in_zone_tie_breaks_to_higher_intensity():
    row = pd.Series(
        {
            "minutes_light": 10,
            "minutes_moderate": 20,
            "minutes_intense": 20,  # tie with moderate
            "minutes_peak": 0,
        }
    )
    assert infer_zone_from_time_in_zone_row(row) == "intense"


def test_infer_zone_from_avg_hr_bpm_maps_percent_bands():
    cfg = HRZoneInferConfig(max_hr_bpm=200)

    assert infer_zone_from_avg_hr_bpm(110, cfg) == "light"  # 55%
    assert infer_zone_from_avg_hr_bpm(130, cfg) == "moderate"  # 65%
    assert infer_zone_from_avg_hr_bpm(150, cfg) == "intense"  # 75%
    assert infer_zone_from_avg_hr_bpm(180, cfg) == "peak"  # 90%


def test_infer_missing_zone_does_not_overwrite_existing():
    df = pd.DataFrame(
        {
            "did_exercise": ["Yes", "Yes"],
            "heart_rate_zone": ["moderate", "peak"],
            "avg_hr_bpm": [150, 150],
        }
    )
    out = infer_missing_heart_rate_zone(df)
    assert out.loc[0, "heart_rate_zone"] == "moderate"
    assert out.loc[1, "heart_rate_zone"] == "peak"


def test_infer_missing_zone_only_on_exercise_days():
    df = pd.DataFrame(
        {
            "did_exercise": ["No", "Yes"],
            "heart_rate_zone": [pd.NA, pd.NA],
            "avg_hr_bpm": [180, 130],
        }
    )
    out = infer_missing_heart_rate_zone(df, cfg=HRZoneInferConfig(max_hr_bpm=200))
    # rest day remains unknown? your function sets unknown for exercise-day missing only;
    # rest day keeps NA
    assert pd.isna(out.loc[0, "heart_rate_zone"])
    assert out.loc[1, "heart_rate_zone"] == "moderate"

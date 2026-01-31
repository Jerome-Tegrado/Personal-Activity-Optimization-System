import pandas as pd

from paos.experiments.effects import compute_experiment_effects


def test_compute_experiment_effects_basic():
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
            "experiment": ["lunch-walk", "lunch-walk", "lunch-walk", "lunch-walk"],
            "experiment_phase": ["control", "control", "treatment", "treatment"],
            "activity_level": [40, 50, 60, 70],
            "energy_focus": [2, 3, 4, 5],
        }
    )

    out = compute_experiment_effects(df)

    # two metrics => two rows
    assert len(out) == 2

    act = out[out["metric"] == "activity_level"].iloc[0]
    assert act["n_control"] == 2
    assert act["n_treatment"] == 2
    assert act["control_mean"] == 45.0
    assert act["treatment_mean"] == 65.0
    assert act["delta"] == 20.0

    en = out[out["metric"] == "energy_focus"].iloc[0]
    assert en["control_mean"] == 2.5
    assert en["treatment_mean"] == 4.5
    assert en["delta"] == 2.0


def test_compute_experiment_effects_ignores_non_control_treatment():
    df = pd.DataFrame(
        {
            "experiment": ["x", "x", "x"],
            "experiment_phase": ["control", "washout", "treatment"],
            "activity_level": [10, 999, 30],
            "energy_focus": [1, 5, 3],
        }
    )

    out = compute_experiment_effects(df)

    act = out[out["metric"] == "activity_level"].iloc[0]
    assert act["n_control"] == 1
    assert act["n_treatment"] == 1
    assert act["control_mean"] == 10.0
    assert act["treatment_mean"] == 30.0
    assert act["delta"] == 20.0

import pandas as pd

import paos.transform.scoring as scoring


def _pick_fn(module, names):
    for name in names:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    raise RuntimeError(
        f"Could not find an enrich function in {module.__name__}. Tried: {', '.join(names)}"
    )


def test_steps_only_sets_exercise_points_zero():
    enrich_fn = _pick_fn(scoring, ("enrich_daily_log", "enrich", "score_and_enrich", "add_scores"))

    # Minimal (steps-only) shape: no exercise_* columns at all
    df = pd.DataFrame(
        [
            {
                "date": "2026-01-14",
                "steps": 6500,
                "energy_focus": 3,
                "did_exercise": "No",
            }
        ]
    )

    out = enrich_fn(df)

    assert int(out.loc[0, "exercise_points"]) == 0
    assert int(out.loc[0, "activity_level"]) == int(out.loc[0, "step_points"]) + 0


def test_step_points_boundaries():
    enrich_fn = _pick_fn(scoring, ("enrich_daily_log", "enrich", "score_and_enrich", "add_scores"))

    df = pd.DataFrame(
        [
            {"date": "2026-01-01", "steps": 4999, "energy_focus": 3, "did_exercise": "No"},
            {"date": "2026-01-02", "steps": 5000, "energy_focus": 3, "did_exercise": "No"},
            {"date": "2026-01-03", "steps": 6999, "energy_focus": 3, "did_exercise": "No"},
            {"date": "2026-01-04", "steps": 7000, "energy_focus": 3, "did_exercise": "No"},
            {"date": "2026-01-05", "steps": 9999, "energy_focus": 3, "did_exercise": "No"},
            {"date": "2026-01-06", "steps": 10000, "energy_focus": 3, "did_exercise": "No"},
        ]
    )

    out = enrich_fn(df)
    assert out["step_points"].astype(int).tolist() == [10, 25, 25, 35, 35, 50]

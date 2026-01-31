from __future__ import annotations

from paos.transform.recommendations import recommend


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

from __future__ import annotations

# Step scoring (0-50)
STEP_BANDS = [
    (0, 4999, 10),
    (5000, 6999, 25),
    (7000, 9999, 35),
    (10000, 10**9, 50),
]

# Exercise scoring (0-50)
DURATION_BANDS = [
    (0, 19, 10),
    (20, 39, 25),
    (40, 60, 35),
    (61, 10**9, 45),
]

HR_MULTIPLIERS = {
    "light": 0.5,
    "moderate": 1.0,
    "intense": 1.5,
    "peak": 2.0,
    "unknown": 1.0,
}

STATUS_BANDS = [
    (0, 25, "Sedentary"),
    (26, 50, "Lightly Active"),
    (51, 75, "Active"),
    (76, 100, "Very Active"),
]

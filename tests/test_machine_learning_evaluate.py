import pandas as pd

from paos.machine_learning.evaluate import evaluate_energy_model, time_based_split


def _make_Xy(n=20):
    # X: simple monotonic activity pattern (time ordered)
    X = pd.DataFrame(
        {
            "steps": [5000 + i * 100 for i in range(n)],
            "activity_level": [20 + i for i in range(n)],
            "day_of_week": [i % 7 for i in range(n)],
            "is_weekend": [1 if (i % 7) >= 5 else 0 for i in range(n)],
            "activity_level_lag_1": [19 + i for i in range(n)],
            "activity_level_rollmean_7": [20 + i for i in range(n)],
        }
    )

    # y: correlated with activity (1..5)
    y = pd.Series([min(5, max(1, 1 + (i // 5))) for i in range(n)])
    return X, y


def test_time_based_split_sizes():
    X, y = _make_Xy(20)
    Xtr, Xte, ytr, yte = time_based_split(X, y, test_size=0.2)

    assert len(Xtr) == 16
    assert len(Xte) == 4
    assert len(ytr) == 16
    assert len(yte) == 4


def test_evaluate_energy_model_returns_metrics():
    X, y = _make_Xy(30)
    r = evaluate_energy_model(X, y, model_type="ridge", test_size=0.2)

    assert r.n_train > 0
    assert r.n_test > 0
    assert r.mae >= 0
    assert r.rmse >= 0
    assert r.baseline_mae >= 0
    assert r.baseline_rmse >= 0

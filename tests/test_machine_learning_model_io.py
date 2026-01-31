from pathlib import Path

import numpy as np
import pandas as pd

from paos.machine_learning.model import (
    BaselineMeanModel,
    load_model,
    predict_energy,
    save_model,
    train_energy_model,
)


def test_baseline_model_predicts_mean():
    X = pd.DataFrame({"a": [1, 2, 3], "b": [0, 0, 1]})
    y = pd.Series([2, 4, 6])

    model = train_energy_model(X, y, model_type="baseline")
    preds = predict_energy(model, X, clip_range=None)

    assert isinstance(model, BaselineMeanModel)
    assert preds.shape == (3,)
    assert np.allclose(preds, np.mean(y))


def test_save_and_load_baseline_model(tmp_path: Path):
    X = pd.DataFrame({"a": [1, 2, 3]})
    y = pd.Series([1, 3, 5])

    model = train_energy_model(X, y, model_type="baseline")

    out = tmp_path / "energy_model.pkl"
    save_model(model, out)

    loaded = load_model(out)
    preds1 = predict_energy(model, X, clip_range=None)
    preds2 = predict_energy(loaded, X, clip_range=None)

    assert np.allclose(preds1, preds2)


def test_predict_energy_clips_to_scale():
    X = pd.DataFrame({"a": [1, 2, 3]})
    model = BaselineMeanModel(y_mean_=999.0)

    preds = predict_energy(model, X)  # default clip (1,5)
    assert preds.min() >= 1.0
    assert preds.max() <= 5.0

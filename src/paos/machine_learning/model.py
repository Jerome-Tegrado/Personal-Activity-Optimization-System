from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import numpy as np
import pandas as pd

try:
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import RandomForestRegressor
except Exception as e:  # pragma: no cover
    Ridge = None
    RandomForestRegressor = None


@dataclass
class BaselineMeanModel:
    """
    Baseline model that predicts the mean of y from the training set.

    This is used to prove that any ML model is better than a trivial baseline.
    """
    y_mean_: float

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.full(shape=(len(X),), fill_value=float(self.y_mean_), dtype=float)


def train_energy_model(
    X: pd.DataFrame,
    y: pd.Series,
    model_type: str = "ridge",
    random_state: int = 42,
    ridge_alpha: float = 1.0,
    rf_n_estimators: int = 200,
) -> Any:
    """
    Train an Energy/Focus regression model.

    Parameters
    ----------
    X, y:
        Training features and target.
    model_type:
        "ridge" (default) or "rf" (RandomForest).
    random_state:
        Used for reproducibility where applicable.
    ridge_alpha:
        Ridge regularization strength.
    rf_n_estimators:
        Number of trees for RandomForest.

    Returns
    -------
    model:
        A fitted model with a .predict method.
    """
    if len(X) == 0:
        raise ValueError("X is empty; cannot train a model.")
    if len(y) == 0:
        raise ValueError("y is empty; cannot train a model.")
    if len(X) != len(y):
        raise ValueError(f"X and y length mismatch: {len(X)} vs {len(y)}")

    model_type = model_type.strip().lower()

    if model_type == "baseline":
        return BaselineMeanModel(y_mean_=float(np.mean(y)))

    if model_type == "ridge":
        if Ridge is None:
            raise ImportError("scikit-learn is required for Ridge. Install scikit-learn.")
        model = Ridge(alpha=ridge_alpha, random_state=random_state)
        model.fit(X.values, y.values)
        return model

    if model_type in {"rf", "randomforest", "random_forest"}:
        if RandomForestRegressor is None:
            raise ImportError("scikit-learn is required for RandomForestRegressor. Install scikit-learn.")
        model = RandomForestRegressor(
            n_estimators=rf_n_estimators,
            random_state=random_state,
            n_jobs=-1,
        )
        model.fit(X.values, y.values)
        return model

    raise ValueError(f"Unknown model_type='{model_type}'. Use 'baseline', 'ridge', or 'rf'.")


def predict_energy(model: Any, X: pd.DataFrame, clip_range: tuple[float, float] | None = (1.0, 5.0)) -> np.ndarray:
    """
    Predict Energy/Focus given a trained model and features.

    clip_range defaults to (1, 5) because energy_focus is a 1–5 scale.
    """
    if len(X) == 0:
        return np.array([], dtype=float)

    # Support both our baseline dataclass and sklearn-like estimators
    if hasattr(model, "predict"):
        preds = model.predict(X if isinstance(model, BaselineMeanModel) else X.values)
    else:
        raise TypeError("Model does not have a .predict method.")

    preds = np.asarray(preds, dtype=float)

    if clip_range is not None:
        lo, hi = clip_range
        preds = np.clip(preds, lo, hi)

    return preds


def save_model(model: Any, path: str | Path) -> None:
    """
    Save a trained model to disk.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load_model(path: str | Path) -> Any:
    """
    Load a trained model from disk.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    return joblib.load(path)

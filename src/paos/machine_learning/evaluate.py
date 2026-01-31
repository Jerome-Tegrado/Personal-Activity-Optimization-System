from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from .model import predict_energy, train_energy_model


@dataclass(frozen=True)
class EvalResult:
    model_type: str
    n_train: int
    n_test: int
    mae: float
    rmse: float
    baseline_mae: float
    baseline_rmse: float
    mae_improvement: float
    rmse_improvement: float


def time_based_split(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Time-ordered split (good default for daily logs).
    Assumes X/y are already aligned in time order.
    """
    if not (0.0 < test_size < 1.0):
        raise ValueError("test_size must be between 0 and 1 (exclusive).")

    n = len(X)
    if n < 5:
        raise ValueError("Not enough rows to split (need at least 5).")

    split_idx = int(np.floor(n * (1.0 - test_size)))
    if split_idx <= 0 or split_idx >= n:
        raise ValueError("Split resulted in empty train or test set.")

    X_train = X.iloc[:split_idx].reset_index(drop=True)
    y_train = y.iloc[:split_idx].reset_index(drop=True)
    X_test = X.iloc[split_idx:].reset_index(drop=True)
    y_test = y.iloc[split_idx:].reset_index(drop=True)
    return X_train, X_test, y_train, y_test


def _mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def evaluate_energy_model(
    X: pd.DataFrame,
    y: pd.Series,
    model_type: str = "ridge",
    test_size: float = 0.2,
    clip_range: tuple[float, float] | None = (1.0, 5.0),
) -> EvalResult:
    """
    Train + evaluate an Energy/Focus model vs a baseline mean predictor.

    Returns test metrics (MAE/RMSE) + improvement over baseline.
    """
    X_train, X_test, y_train, y_test = time_based_split(X, y, test_size=test_size)

    baseline = train_energy_model(X_train, y_train, model_type="baseline")
    model = train_energy_model(X_train, y_train, model_type=model_type)

    y_true = y_test.to_numpy(dtype=float)
    y_pred_baseline = predict_energy(baseline, X_test, clip_range=clip_range)
    y_pred_model = predict_energy(model, X_test, clip_range=clip_range)

    baseline_mae = _mae(y_true, y_pred_baseline)
    baseline_rmse = _rmse(y_true, y_pred_baseline)

    mae = _mae(y_true, y_pred_model)
    rmse = _rmse(y_true, y_pred_model)

    return EvalResult(
        model_type=model_type,
        n_train=len(X_train),
        n_test=len(X_test),
        mae=mae,
        rmse=rmse,
        baseline_mae=baseline_mae,
        baseline_rmse=baseline_rmse,
        mae_improvement=baseline_mae - mae,
        rmse_improvement=baseline_rmse - rmse,
    )


def eval_result_to_dict(r: EvalResult) -> Dict[str, Any]:
    return asdict(r)

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from .evaluate import eval_result_to_dict, evaluate_energy_model
from .features import EnergyFeatureConfig, build_energy_features
from .model import load_model, predict_energy, save_model, train_energy_model


def train_and_evaluate_from_enriched_csv(
    enriched_csv_path: str | Path,
    model_out_path: str | Path,
    eval_out_path: str | Path | None = None,
    model_type: str = "ridge",
    test_size: float = 0.2,
) -> Dict[str, Any]:
    """
    Train + evaluate an energy model using an enriched CSV (must include energy_focus).
    Saves the model artifact and optionally writes evaluation JSON.
    """
    enriched_csv_path = Path(enriched_csv_path)
    model_out_path = Path(model_out_path)

    df = pd.read_csv(enriched_csv_path)
    X, y, _ = build_energy_features(df)

    # Evaluate on a time-based split
    eval_result = evaluate_energy_model(X, y, model_type=model_type, test_size=test_size)

    # Train final model on ALL available rows (best for actual use)
    model = train_energy_model(X, y, model_type=model_type)
    save_model(model, model_out_path)

    out = eval_result_to_dict(eval_result)

    if eval_out_path is not None:
        eval_out_path = Path(eval_out_path)
        eval_out_path.parent.mkdir(parents=True, exist_ok=True)
        eval_out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    return out


def _build_features_with_mask(
    df: pd.DataFrame,
    config: EnergyFeatureConfig | None = None,
) -> Tuple[pd.DataFrame, pd.Series, list[str], pd.Series]:
    """
    Build features similarly to build_energy_features, but also return the boolean mask
    indicating which rows are valid (i.e., will receive predictions).

    This avoids changing build_energy_features' return signature mid-section.
    """
    cfg = config or EnergyFeatureConfig()

    work = df.copy()
    work[cfg.date_col] = pd.to_datetime(work[cfg.date_col], errors="coerce")
    work = work.sort_values(cfg.date_col).reset_index(drop=True)

    # Ensure activity_level exists (compute if possible)
    if cfg.activity_level_col not in work.columns:
        if cfg.step_points_col in work.columns and cfg.exercise_points_col in work.columns:
            work[cfg.activity_level_col] = pd.to_numeric(
                work[cfg.step_points_col], errors="coerce"
            ).fillna(0).astype(float) + pd.to_numeric(
                work[cfg.exercise_points_col], errors="coerce"
            ).fillna(0).astype(float)
        else:
            raise ValueError(
                "Missing 'activity_level' and cannot compute it because "
                "'step_points' and/or 'exercise_points' are missing."
            )

    # Numeric hygiene
    work[cfg.steps_col] = pd.to_numeric(work[cfg.steps_col], errors="coerce")
    work[cfg.activity_level_col] = pd.to_numeric(work[cfg.activity_level_col], errors="coerce")

    # Context features
    work["day_of_week"] = work[cfg.date_col].dt.dayofweek.astype(int)
    work["is_weekend"] = (work["day_of_week"] >= 5).astype(int)

    if cfg.step_points_col in work.columns:
        work[cfg.step_points_col] = pd.to_numeric(work[cfg.step_points_col], errors="coerce")
    if cfg.exercise_points_col in work.columns:
        work[cfg.exercise_points_col] = pd.to_numeric(
            work[cfg.exercise_points_col], errors="coerce"
        )

    # Leakage-safe time features
    work["activity_level_lag_1"] = work[cfg.activity_level_col].shift(1)
    work["activity_level_rollmean_7"] = (
        work[cfg.activity_level_col]
        .shift(1)
        .rolling(window=cfg.rolling_window_days, min_periods=1)
        .mean()
    )

    # Match the same feature selection logic as build_energy_features
    feature_names: list[str] = [
        cfg.steps_col,
        cfg.activity_level_col,
        "day_of_week",
        "is_weekend",
        "activity_level_lag_1",
        "activity_level_rollmean_7",
    ]
    if cfg.step_points_col in work.columns:
        feature_names.insert(1, cfg.step_points_col)
    if cfg.exercise_points_col in work.columns:
        insert_at = 2 if cfg.step_points_col in work.columns else 1
        feature_names.insert(insert_at, cfg.exercise_points_col)

    X_all = work[feature_names].copy()
    y_all = (
        pd.to_numeric(work[cfg.target_col], errors="coerce")
        if cfg.target_col in work.columns
        else pd.Series(np.nan, index=work.index)
    )

    valid_mask = ~X_all.isna().any(axis=1)
    # If target exists (training), require it too
    if cfg.target_col in work.columns:
        valid_mask = valid_mask & (~y_all.isna())

    X_valid = X_all.loc[valid_mask].reset_index(drop=True)
    y_valid = y_all.loc[valid_mask].reset_index(drop=True)

    return X_valid, y_valid, feature_names, valid_mask


def predict_energy_into_csv(
    enriched_csv_path: str | Path,
    model_path: str | Path,
    out_csv_path: str | Path,
    pred_col: str = "energy_focus_pred",
) -> None:
    """
    Load a trained model and write predictions into a copy of the enriched CSV.
    Rows without valid features (e.g., first row due to lag) will keep NaN predictions.
    """
    enriched_csv_path = Path(enriched_csv_path)
    out_csv_path = Path(out_csv_path)

    df = pd.read_csv(enriched_csv_path)

    # Build features + mask on a sorted copy (canonical time order)
    cfg = EnergyFeatureConfig()
    df_sorted = df.copy()
    df_sorted[cfg.date_col] = pd.to_datetime(df_sorted[cfg.date_col], errors="coerce")
    df_sorted = df_sorted.sort_values(cfg.date_col).reset_index(drop=True)

    X_valid, _, _, valid_mask = _build_features_with_mask(df_sorted, config=cfg)

    model = load_model(model_path)
    preds = predict_energy(model, X_valid)  # default clip to [1,5]

    df_sorted[pred_col] = np.nan
    df_sorted.loc[valid_mask, pred_col] = preds

    out_csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_sorted.to_csv(out_csv_path, index=False)

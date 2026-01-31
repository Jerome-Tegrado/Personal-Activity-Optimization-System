from pathlib import Path

import pandas as pd

from paos.machine_learning.cli import (
    predict_energy_into_csv,
    train_and_evaluate_from_enriched_csv,
)


def test_train_and_predict_smoke(tmp_path: Path):
    # Minimal enriched CSV required for features + training
    df = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=14, freq="D").astype(str),
            "steps": [5000 + i * 250 for i in range(14)],
            "activity_level": [20 + i for i in range(14)],
            "energy_focus": [1, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 4, 3, 2],
        }
    )

    enriched_csv = tmp_path / "enriched.csv"
    df.to_csv(enriched_csv, index=False)

    model_path = tmp_path / "models" / "energy_model.pkl"
    eval_path = tmp_path / "reports" / "model" / "energy_eval.json"

    eval_dict = train_and_evaluate_from_enriched_csv(
        enriched_csv_path=enriched_csv,
        model_out_path=model_path,
        eval_out_path=eval_path,
        model_type="ridge",
        test_size=0.2,
    )

    assert model_path.exists()
    assert eval_path.exists()
    assert "mae" in eval_dict
    assert "rmse" in eval_dict
    assert "baseline_mae" in eval_dict

    out_csv = tmp_path / "enriched_with_preds.csv"
    predict_energy_into_csv(
        enriched_csv_path=enriched_csv,
        model_path=model_path,
        out_csv_path=out_csv,
        pred_col="energy_focus_pred",
    )

    assert out_csv.exists()
    df_out = pd.read_csv(out_csv)

    assert "energy_focus_pred" in df_out.columns
    # Some rows will be NaN (lag feature), but not all
    assert df_out["energy_focus_pred"].notna().sum() > 0
    # Preds should respect the scale clip
    non_null = df_out["energy_focus_pred"].dropna()
    assert (non_null >= 1.0).all()
    assert (non_null <= 5.0).all()

"""
Melatih model forecasting beban padam dari data hasil ETL.

Input:
  backend/data/data_beban_padam_up2d.csv

Output:
  backend/model/outage_model_setting_1.pkl
  backend/model/outage_model_setting_2.pkl
  backend/model/outage_scaler_beban.pkl
  backend/model/outage_scaler_fitur.pkl
  backend/data/outage_model_evaluation.json
  backend/data/outage_model_comparison.csv

Split dilakukan kronologis 80% training dan 20% testing. Nilai MAPE dihitung
hanya pada target non-zero karena data beban padam memang dapat bernilai nol.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import MinMaxScaler


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT_DIR / "backend" / "data" / "data_beban_padam_up2d.csv"
MODEL_DIR = ROOT_DIR / "backend" / "model"
OUTPUT_DIR = ROOT_DIR / "backend" / "data"
FEATURES = ["Beban_MW", "Suhu_C", "Jam", "Hari_Minggu", "Bulan", "Adalah_Libur"]
WINDOW = 24
TEST_RATIO = 0.2
SAMPLE_POINTS = 168

SETTINGS = {
    "setting_1": {
        "label": "Setting 1",
        "hidden_layer_sizes": (64, 32),
        "max_iter": 300,
        "learning_rate_init": 0.001,
        "batch_size": 32,
        "alpha": 0.0001,
    },
    "setting_2": {
        "label": "Setting 2",
        "hidden_layer_sizes": (128, 64, 32),
        "max_iter": 500,
        "learning_rate_init": 0.0005,
        "batch_size": 16,
        "alpha": 0.001,
    },
}


def build_windows(frame: pd.DataFrame, feature_scaler: MinMaxScaler, target_scaler: MinMaxScaler):
    features = feature_scaler.fit_transform(frame[FEATURES])
    target = target_scaler.fit_transform(frame[["Beban_MW"]]).ravel()
    x = np.array([features[index - WINDOW : index].flatten() for index in range(WINDOW, len(frame))])
    y = target[WINDOW:]
    return x, y


def evaluate(y_true: np.ndarray, y_pred: np.ndarray, target_scaler: MinMaxScaler) -> dict[str, float]:
    actual = target_scaler.inverse_transform(y_true.reshape(-1, 1)).ravel()
    predicted = target_scaler.inverse_transform(y_pred.reshape(-1, 1)).ravel()
    non_zero = actual > 1e-6
    mape = float(np.mean(np.abs((actual[non_zero] - predicted[non_zero]) / actual[non_zero])) * 100)
    return {
        "mape": round(mape, 4),
        "rmse_mw": round(float(np.sqrt(mean_squared_error(actual, predicted))), 4),
        "mae_mw": round(float(mean_absolute_error(actual, predicted)), 4),
        "r2": round(float(r2_score(actual, predicted)), 6),
        "actual_min_mw": round(float(actual.min()), 4),
        "actual_max_mw": round(float(actual.max()), 4),
        "predicted_min_mw": round(float(predicted.min()), 4),
        "predicted_max_mw": round(float(predicted.max()), 4),
    }


def main() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset tidak ditemukan: {DATA_FILE}")

    frame = pd.read_csv(DATA_FILE, parse_dates=["Waktu"]).sort_values("Waktu").reset_index(drop=True)
    missing = [column for column in FEATURES + ["Waktu"] if column not in frame.columns]
    if missing:
        raise ValueError(f"Kolom dataset tidak lengkap: {missing}")

    feature_scaler = MinMaxScaler()
    target_scaler = MinMaxScaler()
    x, y = build_windows(frame, feature_scaler, target_scaler)
    split = int(len(x) * (1 - TEST_RATIO))
    x_train, x_test = x[:split], x[split:]
    y_train, y_test = y[:split], y[split:]

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with (MODEL_DIR / "outage_scaler_fitur.pkl").open("wb") as handle:
        pickle.dump(feature_scaler, handle)
    with (MODEL_DIR / "outage_scaler_beban.pkl").open("wb") as handle:
        pickle.dump(target_scaler, handle)

    results: dict[str, object] = {
        "dataset": {
            "source": str(DATA_FILE),
            "rows": len(frame),
            "window_hours": WINDOW,
            "features": FEATURES,
            "train_samples": len(x_train),
            "test_samples": len(x_test),
            "split": "chronological_80_20",
        },
        "models": {},
    }
    comparison = []
    for key, setting in SETTINGS.items():
        model = MLPRegressor(
            hidden_layer_sizes=setting["hidden_layer_sizes"],
            activation="relu",
            solver="adam",
            alpha=setting["alpha"],
            batch_size=setting["batch_size"],
            learning_rate_init=setting["learning_rate_init"],
            max_iter=setting["max_iter"],
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=20,
            random_state=42,
        )
        model.fit(x_train, y_train)
        prediction = np.clip(model.predict(x_test), 0.0, None)
        metrics = evaluate(y_test, prediction, target_scaler)
        actual = target_scaler.inverse_transform(y_test.reshape(-1, 1)).ravel()
        predicted = target_scaler.inverse_transform(prediction.reshape(-1, 1)).ravel()
        sample = [
            {
                "index": int(split + index),
                "waktu": frame.iloc[WINDOW + split + index]["Waktu"].strftime("%Y-%m-%d %H:%M"),
                "aktual_mw": round(float(actual[index]), 4),
                "prediksi_mw": round(float(predicted[index]), 4),
            }
            for index in range(min(SAMPLE_POINTS, len(actual)))
        ]
        model_file = MODEL_DIR / f"outage_model_{key}.pkl"
        with model_file.open("wb") as handle:
            pickle.dump(model, handle)
        results["models"][key] = {
            "label": setting["label"],
            "architecture": list(setting["hidden_layer_sizes"]),
            "epochs": int(model.n_iter_),
            "metrics": metrics,
            "sample": sample,
            "model_file": str(model_file),
        }
        comparison.append(
            {
                "Setting": setting["label"],
                "Arsitektur": str(setting["hidden_layer_sizes"]),
                "MAPE (%)": metrics["mape"],
                "RMSE (MW)": metrics["rmse_mw"],
                "MAE (MW)": metrics["mae_mw"],
                "R2": metrics["r2"],
                "Epoch": int(model.n_iter_),
            }
        )
        print(
            f"{setting['label']}: MAPE={metrics['mape']:.4f}% "
            f"RMSE={metrics['rmse_mw']:.4f} MW R2={metrics['r2']:.6f}"
        )

    with (OUTPUT_DIR / "outage_model_evaluation.json").open("w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2)
    pd.DataFrame(comparison).to_csv(OUTPUT_DIR / "outage_model_comparison.csv", index=False)
    print(f"Evaluasi disimpan ke {OUTPUT_DIR / 'outage_model_evaluation.json'}")


if __name__ == "__main__":
    main()

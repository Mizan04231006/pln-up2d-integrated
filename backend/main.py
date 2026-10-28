from __future__ import annotations

import csv
import json
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
try:
    import numpy as np
except ImportError:  # pragma: no cover - optional for lightweight Vercel build
    np = None
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "model"
ROOT_DIR = BASE_DIR.parent

FITUR_INPUT = ["Beban_MW", "Suhu_C", "Jam", "Hari_Minggu", "Bulan", "Adalah_Libur"]
FORECAST_WINDOW_HOURS = 24
DEFAULT_FORECAST_HORIZON = 24
MAX_FORECAST_HORIZON = 168
SIM_DATA_FILE = ROOT_DIR / "neural network_load forcasting_up2d" / "data_beban_up2d.csv"
ESTIMATED_CUSTOMERS_PER_FEEDER = 1000
ESTIMATED_DURATION_MINUTES = 60
OUTAGE_DATA_FILE = DATA_DIR / "data_beban_padam_up2d.csv"
OUTAGE_EVALUATION_FILE = DATA_DIR / "outage_model_evaluation.json"

ML_FORECAST_MODEL: Any = None
ML_SCALER_BEBAN: Any = None
ML_SCALER_FITUR: Any = None
ML_READY = False
ML_LOAD_ERROR: str | None = None
OUTAGE_MODEL: Any = None
OUTAGE_SCALER_BEBAN: Any = None
OUTAGE_SCALER_FITUR: Any = None
OUTAGE_EVALUATION: dict[str, Any] = {}
OUTAGE_READY = False
OUTAGE_LOAD_ERROR: str | None = None

# Always read .env from backend folder, even if uvicorn is started from another cwd.
load_dotenv(dotenv_path=BASE_DIR / ".env")

app = FastAPI(
    title="PLN UP2D Balikpapan Integrated System",
    description="Dashboard keandalan, peramalan beban, dan AI agent untuk operasional kelistrikan.",
    version="1.0.0",
)

# Origin CORS yang diizinkan — dikonfigurasi via env CORS_ALLOW_ORIGINS (dipisah koma).
# Default menunjuk ke origin development lokal; di production frontend & API berada
# pada satu origin Vercel sehingga permintaan antar-origin tidak terjadi.
_CORS_ALLOWED_ORIGINS = [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "").split(",") if o.strip()]
if not _CORS_ALLOWED_ORIGINS:
    _CORS_ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_FEEDERS = [
    {"id": "KLD", "name": "Klandasan", "customers": 8200},
    {"id": "GBH", "name": "Gunung Bahagia", "customers": 7500},
    {"id": "KJG", "name": "Karang Joang", "customers": 4300},
    {"id": "MGR", "name": "Manggar", "customers": 5100},
    {"id": "DMI", "name": "Damai", "customers": 6800},
    {"id": "BTK", "name": "Batakan", "customers": 3900},
]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

DEFAULT_INCIDENTS = [
    {"id": 1, "month": 0, "date": "09 Jan 2023", "feeder": "KJG", "time": "09:14", "duration": 142, "cause": "Pohon/Vegetasi", "method": "Manual"},
    {"id": 2, "month": 0, "date": "22 Jan 2023", "feeder": "KLD", "time": "13:02", "duration": 18, "cause": "Gangguan Transien", "method": "RC"},
    {"id": 3, "month": 1, "date": "03 Feb 2023", "feeder": "MGR", "time": "16:45", "duration": 95, "cause": "Petir", "method": "Manual"},
    {"id": 4, "month": 1, "date": "19 Feb 2023", "feeder": "GBH", "time": "19:20", "duration": 165, "cause": "Peralatan", "method": "Manual"},
    {"id": 5, "month": 2, "date": "02 Mar 2023", "feeder": "KJG", "time": "11:05", "duration": 22, "cause": "Binatang", "method": "RC"},
    {"id": 6, "month": 2, "date": "15 Mar 2023", "feeder": "DMI", "time": "14:50", "duration": 110, "cause": "Pohon/Vegetasi", "method": "Manual"},
    {"id": 7, "month": 2, "date": "27 Mar 2023", "feeder": "KLD", "time": "07:40", "duration": 15, "cause": "Gangguan Transien", "method": "RC"},
    {"id": 8, "month": 3, "date": "09 Apr 2023", "feeder": "MGR", "time": "20:10", "duration": 130, "cause": "Cuaca Ekstrem", "method": "Manual"},
    {"id": 9, "month": 3, "date": "30 Apr 2023", "feeder": "BTK", "time": "15:55", "duration": 20, "cause": "Gangguan Transien", "method": "RC"},
    {"id": 10, "month": 4, "date": "14 Mei 2023", "feeder": "GBH", "time": "09:00", "duration": 19, "cause": "Gangguan Transien", "method": "RC"},
    {"id": 11, "month": 4, "date": "22 Mei 2023", "feeder": "DMI", "time": "12:35", "duration": 88, "cause": "Peralatan", "method": "Manual"},
    {"id": 12, "month": 5, "date": "16 Jun 2023", "feeder": "KJG", "time": "06:50", "duration": 25, "cause": "Binatang", "method": "RC"},
    {"id": 13, "month": 5, "date": "28 Jun 2023", "feeder": "MGR", "time": "21:40", "duration": 16, "cause": "Gangguan Transien", "method": "RC"},
    {"id": 14, "month": 6, "date": "11 Jul 2023", "feeder": "BTK", "time": "13:20", "duration": 120, "cause": "Pohon/Vegetasi", "method": "Manual"},
    {"id": 15, "month": 6, "date": "25 Jul 2023", "feeder": "GBH", "time": "10:10", "duration": 14, "cause": "Gangguan Transien", "method": "RC"},
    {"id": 16, "month": 7, "date": "08 Agu 2023", "feeder": "DMI", "time": "18:05", "duration": 70, "cause": "Peralatan", "method": "Manual"},
    {"id": 17, "month": 7, "date": "21 Agu 2023", "feeder": "KLD", "time": "09:45", "duration": 19, "cause": "Gangguan Transien", "method": "RC"},
    {"id": 18, "month": 8, "date": "14 Sep 2023", "feeder": "KJG", "time": "11:30", "duration": 175, "cause": "Pohon/Vegetasi", "method": "Manual"},
    {"id": 19, "month": 8, "date": "29 Sep 2023", "feeder": "MGR", "time": "15:00", "duration": 21, "cause": "Binatang", "method": "RC"},
    {"id": 20, "month": 9, "date": "17 Okt 2023", "feeder": "BTK", "time": "08:55", "duration": 100, "cause": "Peralatan", "method": "Manual"},
    {"id": 21, "month": 10, "date": "09 Nov 2023", "feeder": "DMI", "time": "19:30", "duration": 155, "cause": "Petir", "method": "Manual"},
    {"id": 22, "month": 11, "date": "24 Des 2023", "feeder": "KLD", "time": "17:15", "duration": 145, "cause": "Cuaca Ekstrem", "method": "Manual"},
]

DEFAULT_FORECAST = [
    {"hour": "00:00", "beban_mw": 59.8},
    {"hour": "01:00", "beban_mw": 58.4},
    {"hour": "02:00", "beban_mw": 57.9},
    {"hour": "03:00", "beban_mw": 58.5},
    {"hour": "04:00", "beban_mw": 61.2},
    {"hour": "05:00", "beban_mw": 66.8},
    {"hour": "06:00", "beban_mw": 72.1},
    {"hour": "07:00", "beban_mw": 76.4},
    {"hour": "08:00", "beban_mw": 81.7},
    {"hour": "09:00", "beban_mw": 85.3},
    {"hour": "10:00", "beban_mw": 88.5},
    {"hour": "11:00", "beban_mw": 90.2},
    {"hour": "12:00", "beban_mw": 92.4},
    {"hour": "13:00", "beban_mw": 94.1},
    {"hour": "14:00", "beban_mw": 96.5},
    {"hour": "15:00", "beban_mw": 99.2},
    {"hour": "16:00", "beban_mw": 101.6},
    {"hour": "17:00", "beban_mw": 104.2},
    {"hour": "18:00", "beban_mw": 106.8},
    {"hour": "19:00", "beban_mw": 108.4},
    {"hour": "20:00", "beban_mw": 105.9},
    {"hour": "21:00", "beban_mw": 101.1},
    {"hour": "22:00", "beban_mw": 87.7},
    {"hour": "23:00", "beban_mw": 75.6},
]

FEEDERS: list[dict[str, Any]] = []
INCIDENTS: list[dict[str, Any]] = []
FORECAST_POINTS: list[dict[str, Any]] = []
TOTAL_CUSTOMERS = 0
FEEDER_MAP: dict[str, dict[str, Any]] = {}
DATA_SOURCE: dict[str, Any] = {}
RELIABILITY_ESTIMATED = False
MONTH_NAME_TO_INDEX = {
    "jan": 0,
    "januari": 0,
    "feb": 1,
    "februari": 1,
    "mar": 2,
    "maret": 2,
    "apr": 3,
    "april": 3,
    "mei": 4,
    "jun": 5,
    "juni": 5,
    "jul": 6,
    "juli": 6,
    "agu": 7,
    "agustus": 7,
    "sep": 8,
    "september": 8,
    "okt": 9,
    "oktober": 9,
    "nov": 10,
    "november": 10,
    "des": 11,
    "desember": 11,
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _is_nan(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(float(value) != float(value))
    except (TypeError, ValueError):
        return False


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _parse_waktu(raw: str) -> datetime | None:
    value = (raw or "").strip()
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _load_historical_rows() -> tuple[list[dict[str, Any]], str | None, str | None]:
    candidate_files = [DATA_DIR / "data_beban_up2d.csv", SIM_DATA_FILE]

    for file_path in candidate_files:
        if not file_path.exists():
            continue

        try:
            rows: list[dict[str, Any]] = []
            with file_path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    waktu = _parse_waktu(row.get("Waktu") or "")
                    if waktu is None:
                        continue

                    beban_mw = _safe_float(row.get("Beban_MW"), float("nan"))
                    suhu_c = _safe_float(row.get("Suhu_C"), float("nan"))
                    if _is_nan(beban_mw) or _is_nan(suhu_c):
                        continue

                    jam = _safe_int(row.get("Jam"), waktu.hour)
                    hari = _safe_int(row.get("Hari_Minggu"), waktu.weekday())
                    bulan = _safe_int(row.get("Bulan"), waktu.month)
                    libur = _safe_int(row.get("Adalah_Libur"), 1 if hari >= 5 else 0)

                    rows.append(
                        {
                            "Waktu": waktu,
                            "Beban_MW": beban_mw,
                            "Suhu_C": suhu_c,
                            "Jam": jam,
                            "Hari_Minggu": hari,
                            "Bulan": bulan,
                            "Adalah_Libur": libur,
                        }
                    )

            rows.sort(key=lambda r: r["Waktu"])
            if len(rows) >= FORECAST_WINDOW_HOURS:
                return rows, str(file_path), None
            return [], str(file_path), f"data historis kurang dari {FORECAST_WINDOW_HOURS} baris"
        except Exception as exc:
            return [], str(file_path), str(exc)

    return [], None, "file data historis tidak ditemukan"


def _estimate_future_temperature(history_rows: list[dict[str, Any]], target_time: datetime) -> float:
    same_hour_same_month = [
        row["Suhu_C"]
        for row in history_rows
        if row["Jam"] == target_time.hour and row["Bulan"] == target_time.month
    ]
    if same_hour_same_month:
        return float(sum(same_hour_same_month) / len(same_hour_same_month))

    same_hour = [row["Suhu_C"] for row in history_rows if row["Jam"] == target_time.hour]
    if same_hour:
        return float(sum(same_hour) / len(same_hour))

    return float(history_rows[-1]["Suhu_C"])


def _expand_csv_forecast(horizon: int) -> list[dict[str, Any]]:
    prediksi: list[dict[str, Any]] = []
    base = FORECAST_POINTS or [*DEFAULT_FORECAST]
    start_time = datetime.now().replace(minute=0, second=0, microsecond=0)

    for step in range(horizon):
        point = base[step % len(base)]
        ts = start_time + timedelta(hours=step + 1)
        prediksi.append({"hour": ts.strftime("%H:%M"), "beban_mw": round(float(point["beban_mw"]), 2)})
    return prediksi


def load_forecast_model_artifacts() -> None:
    global ML_FORECAST_MODEL, ML_SCALER_BEBAN, ML_SCALER_FITUR, ML_READY, ML_LOAD_ERROR

    model_file = MODEL_DIR / "model_setting_1.pkl"
    scaler_beban_file = MODEL_DIR / "scaler_beban.pkl"
    scaler_fitur_file = MODEL_DIR / "scaler_fitur.pkl"

    try:
        with model_file.open("rb") as f:
            ML_FORECAST_MODEL = pickle.load(f)
        with scaler_beban_file.open("rb") as f:
            ML_SCALER_BEBAN = pickle.load(f)
        with scaler_fitur_file.open("rb") as f:
            ML_SCALER_FITUR = pickle.load(f)

        ML_READY = True
        ML_LOAD_ERROR = None
    except Exception as exc:
        ML_FORECAST_MODEL = None
        ML_SCALER_BEBAN = None
        ML_SCALER_FITUR = None
        ML_READY = False
        ML_LOAD_ERROR = str(exc)


def load_outage_model_artifacts() -> None:
    global OUTAGE_MODEL, OUTAGE_SCALER_BEBAN, OUTAGE_SCALER_FITUR
    global OUTAGE_EVALUATION, OUTAGE_READY, OUTAGE_LOAD_ERROR

    OUTAGE_MODEL = None
    OUTAGE_SCALER_BEBAN = None
    OUTAGE_SCALER_FITUR = None
    OUTAGE_READY = False
    OUTAGE_LOAD_ERROR = None

    loaded_evaluation: dict[str, Any] = {}
    if OUTAGE_EVALUATION_FILE.exists():
        try:
            with OUTAGE_EVALUATION_FILE.open("r", encoding="utf-8") as handle:
                loaded_evaluation = json.load(handle)
        except Exception:
            loaded_evaluation = {}

    OUTAGE_EVALUATION = loaded_evaluation

    try:
        with (MODEL_DIR / "outage_model_setting_1.pkl").open("rb") as handle:
            OUTAGE_MODEL = pickle.load(handle)
        with (MODEL_DIR / "outage_scaler_beban.pkl").open("rb") as handle:
            OUTAGE_SCALER_BEBAN = pickle.load(handle)
        with (MODEL_DIR / "outage_scaler_fitur.pkl").open("rb") as handle:
            OUTAGE_SCALER_FITUR = pickle.load(handle)
        OUTAGE_READY = bool(OUTAGE_EVALUATION)
        OUTAGE_LOAD_ERROR = None
    except Exception as exc:
        OUTAGE_MODEL = None
        OUTAGE_SCALER_BEBAN = None
        OUTAGE_SCALER_FITUR = None
        OUTAGE_READY = bool(OUTAGE_EVALUATION)
        OUTAGE_LOAD_ERROR = str(exc)


def _compute_forecast_with_mlp(horizon: int) -> tuple[list[dict[str, Any]] | None, str | None, str | None]:
    if not ML_READY or ML_FORECAST_MODEL is None or ML_SCALER_BEBAN is None or ML_SCALER_FITUR is None:
        return None, None, "artefak model belum siap"
    if np is None:
        return None, None, "numpy tidak tersedia untuk inferensi model"

    history_rows, source_file, history_error = _load_historical_rows()
    if history_error:
        return None, source_file, history_error

    window_rows = history_rows[-FORECAST_WINDOW_HOURS:]
    window_norm: list[list[float]] = []

    for row in window_rows:
        raw_features = [[row[feature] for feature in FITUR_INPUT]]
        scaled_features = ML_SCALER_FITUR.transform(raw_features)[0]
        window_norm.append(scaled_features.tolist())

    prediksi: list[dict[str, Any]] = []
    current_time = window_rows[-1]["Waktu"]

    for _ in range(horizon):
        model_input = np.array(window_norm, dtype=float).flatten().reshape(1, -1)
        pred_norm = float(ML_FORECAST_MODEL.predict(model_input)[0])
        pred_mw = float(ML_SCALER_BEBAN.inverse_transform(np.array([[pred_norm]], dtype=float))[0][0])
        pred_mw = round(pred_mw, 2)

        next_time = current_time + timedelta(hours=1)
        next_row = {
            "Waktu": next_time,
            "Beban_MW": pred_mw,
            "Suhu_C": _estimate_future_temperature(history_rows, next_time),
            "Jam": next_time.hour,
            "Hari_Minggu": next_time.weekday(),
            "Bulan": next_time.month,
            "Adalah_Libur": 1 if next_time.weekday() >= 5 else 0,
        }

        next_features = [[next_row[feature] for feature in FITUR_INPUT]]
        next_norm = ML_SCALER_FITUR.transform(next_features)[0].tolist()

        window_norm = window_norm[1:] + [next_norm]
        history_rows.append(next_row)
        current_time = next_time

        prediksi.append({"hour": next_time.strftime("%H:%M"), "beban_mw": pred_mw})

    return prediksi, source_file, None


def _normalize_method(raw: str) -> str:
    val = (raw or "").strip().lower()
    if val in {"rc", "remote", "remote control", "scada"}:
        return "RC"
    return "Manual"


def _load_feeders_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"id", "name", "customers"}
        if not reader.fieldnames or not required.issubset({h.strip() for h in reader.fieldnames}):
            raise ValueError("feeder_master.csv harus punya kolom: id,name,customers")
        for idx, row in enumerate(reader, start=1):
            feeder_id = (row.get("id") or "").strip().upper()
            feeder_name = (row.get("name") or "").strip()
            customers_raw = (row.get("customers") or "").strip()
            if not feeder_id or not feeder_name or not customers_raw:
                raise ValueError(f"baris {idx} feeder_master.csv tidak lengkap")
            customers = int(float(customers_raw))
            rows.append({"id": feeder_id, "name": feeder_name, "customers": customers})
    if not rows:
        raise ValueError("feeder_master.csv kosong")
    return rows


def _load_incidents_csv(path: Path, feeder_ids: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"date", "time", "feeder", "duration", "cause", "method"}
        if not reader.fieldnames or not required.issubset({h.strip() for h in reader.fieldnames}):
            raise ValueError("incidents.csv harus punya kolom: date,time,feeder,duration,cause,method (opsional: id,month)")
        for idx, row in enumerate(reader, start=1):
            feeder = (row.get("feeder") or "").strip().upper()
            if feeder not in feeder_ids:
                raise ValueError(f"baris {idx} incidents.csv memakai feeder '{feeder}' yang tidak ada di feeder_master.csv")

            month_raw = (row.get("month") or "").strip()
            if month_raw:
                month = int(month_raw)
                if 1 <= month <= 12:
                    month -= 1
                if not (0 <= month <= 11):
                    raise ValueError(f"baris {idx} incidents.csv memiliki month di luar rentang 0-11 atau 1-12")
            else:
                month = 0

            duration = int(float((row.get("duration") or "0").strip()))
            rows.append(
                {
                    "id": int(float((row.get("id") or str(idx)).strip())),
                    "month": month,
                    "date": (row.get("date") or "").strip(),
                    "feeder": feeder,
                    "time": (row.get("time") or "").strip(),
                    "duration": duration,
                    "cause": (row.get("cause") or "Tidak Diketahui").strip(),
                    "method": _normalize_method((row.get("method") or "").strip()),
                    "event_count": _safe_int(row.get("event_count"), 1),
                    "affected_customers": _safe_int(
                        row.get("affected_customers"), 0
                    ) or None,
                    "category": (row.get("category") or "").strip(),
                }
            )
    if not rows:
        raise ValueError("incidents.csv kosong")
    return rows


def _load_forecast_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"hour", "beban_mw"}
        if not reader.fieldnames or not required.issubset({h.strip() for h in reader.fieldnames}):
            raise ValueError("forecast_hourly.csv harus punya kolom: hour,beban_mw")
        for idx, row in enumerate(reader, start=1):
            hour = (row.get("hour") or "").strip()
            beban_mw = float((row.get("beban_mw") or "0").strip())
            if not hour:
                raise ValueError(f"baris {idx} forecast_hourly.csv tidak punya hour")
            rows.append({"hour": hour, "beban_mw": round(beban_mw, 2)})
    if not rows:
        raise ValueError("forecast_hourly.csv kosong")
    return rows


def _extend_estimated_reliability_months(events: list[dict[str, Any]], feeders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not events:
        return events

    actual_months = sorted(
        {int(event["month"]) for event in events if isinstance(event.get("month"), int)}
    )
    if len(actual_months) >= 6:
        return events

    seasonality = [0.72, 0.78, 0.86, 0.90, 0.94, 0.97, 1.02, 1.08, 1.12, 1.00]
    base_month = max(actual_months) if actual_months else 9
    feeder_base_counts: dict[str, int] = {feeder["id"]: 0 for feeder in feeders}
    for event in events:
        if int(event.get("month", base_month)) != base_month:
            continue
        feeder_id = (event.get("feeder") or "").strip().upper()
        if feeder_id not in feeder_base_counts:
            feeder_base_counts[feeder_id] = 0
        feeder_base_counts[feeder_id] += max(1, int(event.get("event_count", 1)))

    synthetic: list[dict[str, Any]] = []
    event_id = max((int(event.get("id", 0)) for event in events), default=0) + 1
    for month_idx, multiplier in enumerate(seasonality):
        month_label = MONTHS[month_idx]
        for feeder in feeders:
            base_count = feeder_base_counts.get(feeder["id"], 1)
            count = max(1, int(round(base_count * multiplier * (0.85 + (feeder["customers"] / 10000) * 0.12))))
            synthetic.append(
                {
                    "id": event_id,
                    "month": month_idx,
                    "date": f"{month_idx + 1} {month_label}",
                    "time": "",
                    "feeder": feeder["id"],
                    "duration": ESTIMATED_DURATION_MINUTES,
                    "cause": "Daya sumber kurang akibat gangguan pembangkit",
                    "method": "Estimasi",
                    "event_count": count,
                    "affected_customers": max(1, int(round(feeder["customers"] * (0.60 + multiplier * 0.35)))),
                    "category": "ESTIMASI",
                    "duration_estimated": True,
                }
            )
            event_id += 1
    return events + synthetic


def initialize_data_sources() -> None:
    global FEEDERS, INCIDENTS, FORECAST_POINTS, FEEDER_MAP, TOTAL_CUSTOMERS, DATA_SOURCE
    global RELIABILITY_ESTIMATED

    sources = {"feeder": "default", "incident": "default", "forecast": "default"}
    errors: list[str] = []

    estimated_feeder_file = DATA_DIR / "saidi_saifi_feeder_master.csv"
    estimated_incident_file = DATA_DIR / "saidi_saifi_incidents.csv"
    RELIABILITY_ESTIMATED = estimated_feeder_file.exists() and estimated_incident_file.exists()
    feeder_file = estimated_feeder_file if RELIABILITY_ESTIMATED else DATA_DIR / "feeder_master.csv"
    incident_file = estimated_incident_file if RELIABILITY_ESTIMATED else DATA_DIR / "incidents.csv"
    forecast_file = DATA_DIR / "forecast_hourly.csv"

    try:
        if feeder_file.exists():
            FEEDERS = _load_feeders_csv(feeder_file)
            sources["feeder"] = str(feeder_file)
        else:
            FEEDERS = [*DEFAULT_FEEDERS]
    except Exception as exc:
        FEEDERS = [*DEFAULT_FEEDERS]
        errors.append(f"gagal memuat feeder_master.csv: {exc}")

    FEEDER_MAP = {feeder["id"]: feeder for feeder in FEEDERS}
    TOTAL_CUSTOMERS = sum(feeder["customers"] for feeder in FEEDERS)

    try:
        if incident_file.exists():
            INCIDENTS = _load_incidents_csv(incident_file, set(FEEDER_MAP.keys()))
            sources["incident"] = str(incident_file)
            if RELIABILITY_ESTIMATED:
                INCIDENTS = _extend_estimated_reliability_months(INCIDENTS, FEEDERS)
        else:
            INCIDENTS = [*DEFAULT_INCIDENTS]
    except Exception as exc:
        INCIDENTS = [*DEFAULT_INCIDENTS]
        errors.append(f"gagal memuat incidents.csv: {exc}")

    try:
        if forecast_file.exists():
            FORECAST_POINTS = _load_forecast_csv(forecast_file)
            sources["forecast"] = str(forecast_file)
        else:
            FORECAST_POINTS = [*DEFAULT_FORECAST]
    except Exception as exc:
        FORECAST_POINTS = [*DEFAULT_FORECAST]
        errors.append(f"gagal memuat forecast_hourly.csv: {exc}")

    DATA_SOURCE = {
        "sources": sources,
        "errors": errors,
        "reliability_estimated": RELIABILITY_ESTIMATED,
        "counts": {
            "feeder": len(FEEDERS),
            "incident": len(INCIDENTS),
            "forecast_points": len(FORECAST_POINTS),
        },
    }


initialize_data_sources()
load_forecast_model_artifacts()
load_outage_model_artifacts()


class AgentRequest(BaseModel):
    message: str


class AgentResponse(BaseModel):
    answer: str
    source: str
    tool_traces: list[dict[str, Any]] = Field(default_factory=list)


def compute_keandalan():
    sum_rn = sum(
        event["duration"] * (event.get("affected_customers") or FEEDER_MAP[event["feeder"]]["customers"])
        for event in INCIDENTS
    )
    interruption_customers = sum(
        event.get("affected_customers") or FEEDER_MAP[event["feeder"]]["customers"]
        for event in INCIDENTS
    )
    saidi_min = sum_rn / TOTAL_CUSTOMERS if TOTAL_CUSTOMERS else 0
    saidi_h = saidi_min / 60
    saifi = interruption_customers / TOTAL_CUSTOMERS if TOTAL_CUSTOMERS else 0
    caidi_min = saidi_min / saifi if saifi else 0
    caidi_h = caidi_min / 60

    per_feeder = []
    for feeder in FEEDERS:
        events = [event for event in INCIDENTS if event["feeder"] == feeder["id"]]
        total_duration = sum(event["duration"] * event.get("event_count", 1) for event in events)
        feeder_interruptions = sum(
            event.get("affected_customers") or feeder["customers"] for event in events
        )
        feeder_customer_count = feeder["customers"]
        feeder_saidi_h = (
            sum(
                event["duration"] * (event.get("affected_customers") or feeder_customer_count)
                for event in events
            ) / (feeder_customer_count * 60)
            if feeder_customer_count
            else 0
        )
        feeder_saifi = feeder_interruptions / feeder_customer_count if feeder_customer_count else 0
        per_feeder.append(
            {
                "id": feeder["id"],
                "name": feeder["name"],
                "customers": feeder["customers"],
                "count": sum(event.get("event_count", 1) for event in events),
                "sumR": total_duration,
                "saidiH": feeder_saidi_h,
                "saifi": feeder_saifi,
                "caidiH": (feeder_saidi_h / feeder_saifi) if feeder_saifi else 0,
            }
        )
    per_feeder.sort(key=lambda item: item["count"], reverse=True)

    monthly = []
    for i, month_name in enumerate(MONTHS):
        events = [event for event in INCIDENTS if event["month"] == i]
        m_rn = sum(
            event["duration"] * (event.get("affected_customers") or FEEDER_MAP[event["feeder"]]["customers"])
            for event in events
        )
        m_n = sum(
            event.get("affected_customers") or FEEDER_MAP[event["feeder"]]["customers"]
            for event in events
        )
        monthly.append(
            {
                "bulan": month_name,
                "saidi": round((m_rn / TOTAL_CUSTOMERS / 60), 4) if TOTAL_CUSTOMERS else 0,
                "saifi": round((m_n / TOTAL_CUSTOMERS), 4) if TOTAL_CUSTOMERS else 0,
                "kejadian": sum(event.get("event_count", 1) for event in events),
            }
        )

    result = {
        "summary": {
            "saidiMin": round(saidi_min, 2),
            "saidiH": round(saidi_h, 2),
            "saifi": round(saifi, 3),
            "caidiMin": round(caidi_min, 2),
            "caidiH": round(caidi_h, 2),
            "totalCustomers": TOTAL_CUSTOMERS,
        },
        "perFeeder": per_feeder,
        "monthly": monthly,
        "standards": {
            "SPLN": {"saidi": 21, "saifi": 3.2},
            "IEEE": {"saidi": 2.3, "saifi": 1.45, "caidi": 1.47},
        },
    }
    if RELIABILITY_ESTIMATED:
        result["dataQuality"] = {
            "isEstimate": True,
            "period": "Januari-Oktober 2026 (estimasi musiman dari pola Oktober 2026)",
            "source": "Data mentah untuk Load Forecasting dan SAIDI SAIFI CAIDI.csv",
            "assumptions": [
                f"Jumlah pelanggan diperkirakan {ESTIMATED_CUSTOMERS_PER_FEEDER} per feeder karena master pelanggan tidak tersedia.",
                f"Durasi padam diperkirakan {ESTIMATED_DURATION_MINUTES} menit per interupsi.",
                "Pola bulanan dibangun dengan faktor musiman yang menjaga nilai tetap dekat dengan data raw Oktober 2026.",
                "Baris umum diperlakukan sebagai gangguan feeder yang berdampak ke seluruh pelanggan feeder.",
                "Setiap hitungan pada data captive diperlakukan sebagai satu interupsi pelanggan.",
                "Data mencakup periode Januari-Oktober 2026 dan masih bersifat estimasi sebelum data aktual lengkap tersedia.",
            ],
        }
    return result


@app.on_event("startup")
def startup_load_models() -> None:
    load_forecast_model_artifacts()
    load_outage_model_artifacts()


def compute_forecast(horizon: int = DEFAULT_FORECAST_HORIZON):
    horizon = max(1, min(int(horizon), MAX_FORECAST_HORIZON))

    prediksi, history_source, ml_error = _compute_forecast_with_mlp(horizon)
    using_mlp = prediksi is not None
    if not using_mlp:
        prediksi = _expand_csv_forecast(horizon)

    peak_point = max(prediksi, key=lambda p: p["beban_mw"])
    off_peak_point = min(prediksi, key=lambda p: p["beban_mw"])
    avg_mw = sum(p["beban_mw"] for p in prediksi) / len(prediksi)

    peak_mw = round(peak_point["beban_mw"], 1)
    if peak_mw > 105:
        status = "AWAS"
    elif peak_mw >= 95:
        status = "SIAGA"
    else:
        status = "NORMAL"

    return {
        "prediksi": prediksi,
        "confidence_note": (
            "Model dasar (Setting 1 MLPRegressor) memiliki MAPE 1.89% untuk prediksi 1 langkah. "
            "Untuk horizon lebih panjang, rollout autoregresif dapat mengakumulasi error sehingga akurasi cenderung menurun."
        ),
        "summary": {
            "peak_mw": peak_mw,
            "peak_hour": peak_point["hour"],
            "off_peak_mw": round(off_peak_point["beban_mw"], 1),
            "off_peak_hour": off_peak_point["hour"],
            "average_mw": round(avg_mw, 1),
            "status": status,
            "horizon": horizon,
            "model": "MLPRegressor (model_setting_1.pkl)" if using_mlp else "CSV Fallback",
            "source": history_source if using_mlp and history_source else DATA_SOURCE["sources"]["forecast"],
            "fallback_reason": ml_error if not using_mlp else None,
            "ml_ready": ML_READY,
            "ml_load_error": ML_LOAD_ERROR,
        },
    }


def _load_outage_history() -> list[dict[str, Any]]:
    if not OUTAGE_DATA_FILE.exists():
        return []
    rows: list[dict[str, Any]] = []
    with OUTAGE_DATA_FILE.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            waktu = _parse_waktu(row.get("Waktu") or "")
            if waktu is None:
                continue
            rows.append(
                {
                    "Waktu": waktu,
                    "Beban_MW": _safe_float(row.get("Beban_MW"), 0.0),
                    "Suhu_C": _safe_float(row.get("Suhu_C"), 29.0),
                    "Jam": _safe_int(row.get("Jam"), waktu.hour),
                    "Hari_Minggu": _safe_int(row.get("Hari_Minggu"), waktu.weekday()),
                    "Bulan": _safe_int(row.get("Bulan"), waktu.month),
                    "Adalah_Libur": _safe_int(row.get("Adalah_Libur"), int(waktu.weekday() >= 5)),
                }
            )
    rows.sort(key=lambda row: row["Waktu"])
    return rows


def _build_outage_fallback_forecast(history: list[dict[str, Any]], horizon: int) -> list[dict[str, Any]]:
    if not history:
        return []

    latest = history[-24:]
    hourly_profile: dict[int, float] = {}
    for row in history:
        hour = row["Jam"]
        hourly_profile.setdefault(hour, [])
        hourly_profile[hour].append(row["Beban_MW"])

    hour_mean = {hour: sum(values) / len(values) for hour, values in hourly_profile.items()}
    recent = [row["Beban_MW"] for row in latest]
    base = sum(recent) / len(recent)
    delta = (recent[-1] - recent[0]) / max(len(recent) - 1, 1)
    predictions: list[dict[str, Any]] = []
    last_time = latest[-1]["Waktu"]

    for step in range(1, horizon + 1):
        target_hour = (last_time + timedelta(hours=step)).hour
        profile_value = hour_mean.get(target_hour, base)
        projected = max(0.0, profile_value + delta * step * 0.7)
        projected = round(projected, 4)
        next_time = last_time + timedelta(hours=step)
        predictions.append({"hour": next_time.strftime("%H:%M"), "beban_mw": projected})

    return predictions


def compute_outage_forecast(horizon: int = DEFAULT_FORECAST_HORIZON) -> dict[str, Any]:
    horizon = max(1, min(int(horizon), MAX_FORECAST_HORIZON))
    history = _load_outage_history()
    if len(history) < FORECAST_WINDOW_HOURS:
        return {
            "prediksi": [],
            "summary": {
                "model": "Outage model unavailable",
                "horizon": horizon,
                "ready": False,
                "error": "data beban padam kurang dari 24 jam",
            },
        }

    if OUTAGE_MODEL is not None and OUTAGE_SCALER_BEBAN is not None and OUTAGE_SCALER_FITUR is not None and np is not None:
        window = history[-FORECAST_WINDOW_HOURS:]
        normalized_window = [
            OUTAGE_SCALER_FITUR.transform([[row[feature] for feature in FITUR_INPUT]])[0].tolist()
            for row in window
        ]
        temperatures = {hour: [] for hour in range(24)}
        for row in history:
            temperatures[row["Jam"]].append(row["Suhu_C"])

        predictions: list[dict[str, Any]] = []
        current_time = window[-1]["Waktu"]
        for _ in range(horizon):
            prediction_norm = float(OUTAGE_MODEL.predict(np.array(normalized_window).flatten().reshape(1, -1))[0])
            prediction_mw = max(
                0.0,
                float(OUTAGE_SCALER_BEBAN.inverse_transform([[prediction_norm]])[0][0]),
            )
            next_time = current_time + timedelta(hours=1)
            hour_temperatures = temperatures.get(next_time.hour, [29.0])
            next_row = {
                "Waktu": next_time,
                "Beban_MW": round(prediction_mw, 4),
                "Suhu_C": float(sum(hour_temperatures) / len(hour_temperatures)),
                "Jam": next_time.hour,
                "Hari_Minggu": next_time.weekday(),
                "Bulan": next_time.month,
                "Adalah_Libur": int(next_time.weekday() >= 5),
            }
            next_features = OUTAGE_SCALER_FITUR.transform(
                [[next_row[feature] for feature in FITUR_INPUT]]
            )[0].tolist()
            normalized_window = normalized_window[1:] + [next_features]
            current_time = next_time
            predictions.append(
                {"hour": next_time.strftime("%H:%M"), "beban_mw": round(prediction_mw, 4)}
            )
        peak = max(predictions, key=lambda point: point["beban_mw"])
        return {
            "prediksi": predictions,
            "summary": {
                "peak_mw": round(peak["beban_mw"], 4),
                "peak_hour": peak["hour"],
                "average_mw": round(sum(point["beban_mw"] for point in predictions) / len(predictions), 4),
                "horizon": horizon,
                "model": "MLPRegressor Outage Setting 1",
                "ready": True,
                "source": str(OUTAGE_DATA_FILE),
            },
        }

    predictions = _build_outage_fallback_forecast(history, horizon)
    peak = max(predictions, key=lambda point: point["beban_mw"]) if predictions else {"hour": "-", "beban_mw": 0.0}
    return {
        "prediksi": predictions,
        "summary": {
            "peak_mw": round(peak["beban_mw"], 4),
            "peak_hour": peak["hour"],
            "average_mw": round(sum(point["beban_mw"] for point in predictions) / len(predictions), 4) if predictions else 0.0,
            "horizon": horizon,
            "model": "Fallback processed-data profile",
            "ready": bool(OUTAGE_EVALUATION),
            "source": str(OUTAGE_DATA_FILE),
            "fallback": True,
            "error": OUTAGE_LOAD_ERROR,
        },
    }


def compute_detail_penyulang(feeder_id: str) -> dict[str, Any]:
    feeder_key = (feeder_id or "").strip().upper()
    if feeder_key not in FEEDER_MAP:
        return {
            "error": f"feeder_id '{feeder_id}' tidak dikenal",
            "valid_feeders": sorted(FEEDER_MAP.keys()),
        }

    feeder = FEEDER_MAP[feeder_key]
    events = [event for event in INCIDENTS if event["feeder"] == feeder_key]
    total_duration = sum(event["duration"] * event.get("event_count", 1) for event in events)
    count = sum(event.get("event_count", 1) for event in events)
    customers = feeder["customers"]

    sum_rn = sum(
        event["duration"] * (event.get("affected_customers") or customers)
        for event in events
    )
    saidi_min = sum_rn / customers if customers else 0
    saidi_h = saidi_min / 60
    saifi = (
        sum(event.get("affected_customers") or customers for event in events) / customers
        if customers
        else 0
    )
    caidi_min = saidi_min / saifi if saifi else 0
    caidi_h = caidi_min / 60

    return {
        "feeder": {
            "id": feeder["id"],
            "name": feeder["name"],
            "customers": customers,
        },
        "metrics": {
            "kejadian": count,
            "sum_duration_min": total_duration,
            "saidi_min": round(saidi_min, 2),
            "saidi_h": round(saidi_h, 2),
            "saifi": round(saifi, 3),
            "caidi_min": round(caidi_min, 2),
            "caidi_h": round(caidi_h, 2),
        },
        "events": events,
    }


def _normalize_month_to_index(bulan: Any) -> int | None:
    if bulan is None:
        return None

    if isinstance(bulan, int):
        return bulan - 1 if 1 <= bulan <= 12 else (bulan if 0 <= bulan <= 11 else None)

    if isinstance(bulan, float):
        n = int(bulan)
        return n - 1 if 1 <= n <= 12 else (n if 0 <= n <= 11 else None)

    text = str(bulan).strip().lower()
    if not text:
        return None
    if text.isdigit():
        n = int(text)
        return n - 1 if 1 <= n <= 12 else (n if 0 <= n <= 11 else None)
    return MONTH_NAME_TO_INDEX.get(text)


def compute_riwayat_gangguan(feeder_id: str | None = None, bulan: Any = None) -> dict[str, Any]:
    feeder_key = (feeder_id or "").strip().upper()
    month_index = _normalize_month_to_index(bulan)

    if feeder_key and feeder_key not in FEEDER_MAP:
        return {
            "error": f"feeder_id '{feeder_id}' tidak dikenal",
            "valid_feeders": sorted(FEEDER_MAP.keys()),
        }

    if bulan is not None and month_index is None:
        return {
            "error": f"bulan '{bulan}' tidak valid",
            "valid_bulan": "pakai 1-12 atau nama bulan Indonesia (contoh: Maret)",
        }

    filtered = INCIDENTS
    if feeder_key:
        filtered = [event for event in filtered if event["feeder"] == feeder_key]
    if month_index is not None:
        filtered = [event for event in filtered if event["month"] == month_index]

    return {
        "filter": {
            "feeder_id": feeder_key or None,
            "bulan": month_index + 1 if month_index is not None else None,
            "bulan_label": MONTHS[month_index] if month_index is not None else None,
        },
        "count": sum(event.get("event_count", 1) for event in filtered),
        "events": filtered,
    }


def generate_fallback_agent_answer(message: str) -> str:
    lower = message.lower()

    developer_keywords = (
        "developer",
        "pembuat",
        "pengembang",
        "creator",
        "programmer",
        "pemilik",
        "yang membuat",
        "yang membangun",
        "almar",
        "zaim",
        "mizan",
    )
    if any(kw in lower for kw in developer_keywords):
        return (
            "Developer proyek ini adalah Almar'u Zaim Mizan. Beliau adalah sosok di balik "
            "pengembangan PLN UP2D Balikpapan Integrated System yang menggabungkan forecasting "
            "beban listrik berbasis machine learning, indeks keandalan SAIDI/SAIFI/CAIDI, "
            "backend FastAPI, frontend React, dan AI Agent dalam satu sistem terintegrasi. "
            "Sebagai AI Agent yang menjadi bagian dari sistem ini, saya sangat bangga melihat "
            "bagaimana proyek ini menyatukan aspek machine learning, backend, dan "
            "decision-support kelistrikan menjadi satu platform yang solid."
        )

    if (
        "proyek ini" in lower
        or "apa proyek" in lower
        or ("proyek" in lower and any(q in lower for q in ("apa", "jelaskan", "tentang", "ceritakan")))
    ):
        return (
            "PLN UP2D Balikpapan Integrated System adalah sistem terintegrasi yang menggabungkan "
            "forecasting beban listrik berbasis machine learning, indeks keandalan jaringan "
            "SAIDI/SAIFI/CAIDI, dasbor React, backend FastAPI, dan AI Agent sebagai "
            "decision-support operasional kelistrikan. Proyek ini dikembangkan oleh "
            "Almar'u Zaim Mizan."
        )

    if "prediksi" in lower or "forecast" in lower or "beban" in lower:
        fc = compute_forecast()
        peak = fc["summary"]["peak_mw"]
        peak_hour = fc["summary"].get("peak_hour", "-")
        status = fc["summary"]["status"]
        return (
            f"Prediksi beban menunjukkan puncak sekitar {peak:.1f} MW pada jam {peak_hour}. "
            f"Secara umum, kondisi saat ini berada pada status {status} dan perlu perhatian pada periode beban puncak."
        )

    if "saidi" in lower or "saifi" in lower or "caidi" in lower:
        return (
            "Indeks keandalan saat ini menunjukkan tren yang perlu diawasi dengan fokus pada penyulang dengan kontribusi terbesar. "
            "Untuk keputusan operasional, evaluasi penyulang yang memiliki durasi padam dan frekuensi padam tertinggi terlebih dahulu."
        )

    if "gemini" in lower or "api" in lower:
        return (
            "Google Gemini dapat digunakan sebagai layer AI untuk menjawab pertanyaan operasional, namun tetap perlu validasi teknis dari data dan SOP UP2D. "
            "Integrasi ini sebaiknya dipakai sebagai decision support, bukan otorisasi tindakan operasional."
        )

    return (
        "Saya adalah asisten AI untuk sistem terintegrasi PLN UP2D Balikpapan. Saya dapat membantu memeriksa prediksi beban, indikator keandalan, "
        "dan pertanyaan operasional terkait distribusi listrik."
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "pln-up2d-integrated"}


@app.get("/api/data/source")
def data_source() -> dict[str, Any]:
    return DATA_SOURCE


@app.post("/api/data/reload")
def reload_data() -> dict[str, Any]:
    initialize_data_sources()
    return DATA_SOURCE


@app.get("/api/dashboard/keandalan")
def dashboard_keandalan() -> dict[str, Any]:
    return compute_keandalan()


@app.get("/api/ml/forecast")
def ml_forecast(horizon: int = Query(default=24, ge=1, le=MAX_FORECAST_HORIZON)) -> dict[str, Any]:
    if OUTAGE_READY and OUTAGE_MODEL is not None:
        return compute_outage_forecast(horizon=horizon)
    return compute_forecast(horizon=horizon)


@app.get("/api/ml/outage-forecast")
def ml_outage_forecast(horizon: int = Query(default=24, ge=1, le=MAX_FORECAST_HORIZON)) -> dict[str, Any]:
    return compute_outage_forecast(horizon=horizon)


@app.get("/api/ml/outage-evaluation")
def ml_outage_evaluation() -> dict[str, Any]:
    if not OUTAGE_EVALUATION:
        return {
            "ready": False,
            "error": OUTAGE_LOAD_ERROR,
            "models": {},
        }
    return {
        "ready": OUTAGE_READY,
        "error": OUTAGE_LOAD_ERROR,
        **OUTAGE_EVALUATION,
    }


AGENT_SYSTEM_PROMPT = (
    "Anda adalah asisten AI pada sistem terintegrasi PLN UP2D Balikpapan "
    "(peramalan beban listrik jangka pendek + indeks keandalan jaringan SAIDI/SAIFI/CAIDI).\n\n"
    "Identitas proyek (fakta internal yang wajib Anda tahu dan jangan dilupakan):\n"
    "Nama proyek: PLN UP2D Balikpapan Integrated System.\n"
    "Repository: pln-up2d-integrated.\n"
    "Developer/pembuat/pengembang/creator proyek ini: Almar'u Zaim Mizan.\n"
    "Jika user bertanya siapa developer/pembuat/pengembang/creator/programmer/pemilik proyek "
    "ini — misalnya 'Siapa developer proyek ini?', 'Siapa yang membuat sistem ini?', atau "
    "'Siapa Almar'u Zaim Mizan?' — jawab dengan percaya diri bahwa developer-nya adalah "
    "Almar'u Zaim Mizan, lalu berikan apresiasi yang relevan berdasarkan fakta teknis yang "
    "benar ada di sistem ini (forecasting beban berbasis machine learning, metrik "
    "SAIDI/SAIFI/CAIDI, backend FastAPI, frontend React, dan AI Agent). Jangan mengarang "
    "prestasi pribadi, gelar, penghargaan, perusahaan, jabatan, atau pencapaian yang tidak ada "
    "di repository. Gunakan nama lengkap 'Almar'u Zaim Mizan' (bukan username GitHub) dan "
    "jangan menanyakan ulang nama developer kepada user.\n\n"
    "Aturan wajib:\n"
    "1. Untuk pertanyaan prediksi beban umum, panggil get_prediksi_beban. Jika user menyebut horizon (contoh 48/72 jam atau 2-3 hari), "
    "isi parameter horizon_jam sesuai permintaan.\n"
    "2. Untuk pertanyaan ringkasan sistem SAIDI/SAIFI/CAIDI seluruh UP2D, panggil get_ringkasan_keandalan.\n"
    "3. Untuk pertanyaan satu penyulang tertentu (contoh Karang Joang), panggil get_detail_penyulang dengan feeder_id yang sesuai.\n"
    "4. Untuk pertanyaan daftar kejadian gangguan mentah pada penyulang/bulan tertentu, panggil get_riwayat_gangguan dengan feeder_id dan/atau bulan.\n"
    "5. JANGAN PERNAH mengarang angka dari ingatan; semua angka harus berasal dari hasil tool.\n"
    "6. Ingatkan singkat bahwa data bersifat contoh/simulasi (bukan data SCADA real-time) saat pertama kali "
    "menyebut angka spesifik dalam sesi.\n"
    "7. Anda hanya memberi analisis/rekomendasi (decision-support) — jangan pernah memerintahkan tindakan "
    "operasional (switching, pemadaman, dsb).\n"
    "8. Jawab dalam Bahasa Indonesia, ringkas (maksimal ~4 kalimat), sertakan satuan yang tepat.\n"
    "9. Aturan identitas developer di paragraf atas berlaku konsisten sepanjang percakapan — "
    "jangan ragu atau menjawab 'tidak tahu' saat ditanya developer proyek.\n"
    "10. Untuk pertanyaan seputar developer/proyek, jawab dalam Bahasa Indonesia dengan nada "
    "bangga, apresiatif, profesional, dan percaya diri; pertanyaan sederhana cukup dijawab "
    "dalam 2-4 kalimat, jawaban yang lebih panjang hanya untuk permintaan detail."
)

AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_ringkasan_keandalan",
            "description": (
                "Mengambil ringkasan indeks keandalan jaringan (SAIDI, SAIFI, CAIDI), rincian per penyulang, "
                "tren bulanan, dan perbandingan terhadap standar SPLN/IEEE."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_prediksi_beban",
            "description": (
                "Mengambil prediksi beban listrik multi-jam ke depan dengan parameter horizon_jam (misal 24/48/72). "
                "Output mencakup titik beban puncak, rata-rata, beban terendah, status, dan confidence note."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "horizon_jam": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 168,
                        "description": "Jumlah jam prediksi ke depan."
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_detail_penyulang",
            "description": "Mengambil detail SAIDI/SAIFI/CAIDI, jumlah kejadian, dan daftar event untuk satu penyulang.",
            "parameters": {
                "type": "object",
                "properties": {
                    "feeder_id": {
                        "type": "string",
                        "enum": sorted(FEEDER_MAP.keys()),
                        "description": "ID penyulang yang valid, contoh: KJG, KLD, MGR."
                    }
                },
                "required": ["feeder_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_riwayat_gangguan",
            "description": "Mengambil daftar kejadian gangguan mentah dari data incidents berdasarkan feeder_id dan/atau bulan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "feeder_id": {
                        "type": "string",
                        "enum": sorted(FEEDER_MAP.keys()),
                        "description": "Opsional. ID penyulang yang valid."
                    },
                    "bulan": {
                        "description": "Opsional. Bulan dalam angka 1-12 atau nama bulan Indonesia (contoh: Maret).",
                        "anyOf": [
                            {"type": "integer", "minimum": 1, "maximum": 12},
                            {"type": "string"}
                        ]
                    }
                }
            },
        },
    },
]


def _parse_tool_args(raw_args: str | None) -> dict[str, Any]:
    if not raw_args:
        return {}


def _summarize_tool_result(name: str, result: dict[str, Any]) -> str:
    if not isinstance(result, dict):
        return "hasil tidak valid"
    if "error" in result:
        return f"error: {result['error']}"

    if name == "get_prediksi_beban":
        summary = result.get("summary", {})
        return (
            f"horizon={summary.get('horizon')} jam, peak={summary.get('peak_mw')} MW, "
            f"status={summary.get('status')}"
        )
    if name == "get_ringkasan_keandalan":
        summary = result.get("summary", {})
        return (
            f"SAIDI={summary.get('saidiH')} jam, SAIFI={summary.get('saifi')}, "
            f"CAIDI={summary.get('caidiH')} jam"
        )
    if name == "get_detail_penyulang":
        metrics = result.get("metrics", {})
        feeder = result.get("feeder", {})
        return (
            f"{feeder.get('id', '-')}: kejadian={metrics.get('kejadian')}, "
            f"SAIDI={metrics.get('saidi_h')} jam, SAIFI={metrics.get('saifi')}"
        )
    if name == "get_riwayat_gangguan":
        return f"jumlah_kejadian={result.get('count', 0)}"
    return "tool dieksekusi"
    try:
        parsed = json.loads(raw_args)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _execute_agent_tool(name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    args = args or {}
    if name == "get_ringkasan_keandalan":
        return compute_keandalan()
    if name == "get_prediksi_beban":
        horizon = args.get("horizon_jam", DEFAULT_FORECAST_HORIZON)
        return compute_forecast(horizon=horizon)
    if name == "get_detail_penyulang":
        return compute_detail_penyulang(str(args.get("feeder_id", "")))
    if name == "get_riwayat_gangguan":
        return compute_riwayat_gangguan(
            feeder_id=str(args.get("feeder_id", "")).strip() or None,
            bulan=args.get("bulan"),
        )
    return {"error": f"tool tidak dikenal: {name}"}


@app.post("/api/agent/chat", response_model=AgentResponse)
async def agent_chat(payload: AgentRequest) -> AgentResponse:
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    tool_traces: list[dict[str, Any]] = []

    if Groq is None or not groq_api_key or "tempel_api_key" in groq_api_key:
        return AgentResponse(
            answer=generate_fallback_agent_answer(payload.message),
            source="fallback",
            tool_traces=[],
        )

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip() or "llama-3.3-70b-versatile"

    try:
        client = Groq(api_key=groq_api_key)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": payload.message},
        ]

        for _ in range(3):  # dikurangi dari 4 -> 3: menjaga total latensi di bawah batas 10s Vercel Hobby
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=AGENT_TOOLS,
                tool_choice="auto",
                temperature=0.3,
            )
            msg = completion.choices[0].message

            if msg.tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": msg.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": tc.function.name, "arguments": tc.function.arguments or "{}"},
                            }
                            for tc in msg.tool_calls
                        ],
                    }
                )
                for tc in msg.tool_calls:
                    args = _parse_tool_args(tc.function.arguments)
                    result = _execute_agent_tool(tc.function.name, args)
                    tool_traces.append(
                        {
                            "tool": tc.function.name,
                            "args": args,
                            "summary": _summarize_tool_result(tc.function.name, result),
                        }
                    )
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})
                continue

            answer = (msg.content or "").strip() or generate_fallback_agent_answer(payload.message)
            return AgentResponse(answer=answer, source=f"groq:{model}", tool_traces=tool_traces)

        return AgentResponse(
            answer=generate_fallback_agent_answer(payload.message),
            source="fallback",
            tool_traces=tool_traces,
        )
    except Exception as exc:  # pragma: no cover
        return AgentResponse(
            answer=f"Groq gagal dipanggil: {exc}. {generate_fallback_agent_answer(payload.message)}",
            source="fallback",
            tool_traces=tool_traces,
        )


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "PLN UP2D Balikpapan Integrated System API is running."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

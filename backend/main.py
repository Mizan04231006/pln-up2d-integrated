from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Always read .env from backend folder, even if uvicorn is started from another cwd.
load_dotenv(dotenv_path=BASE_DIR / ".env")

app = FastAPI(
    title="PLN UP2D Balikpapan Integrated System",
    description="Dashboard keandalan, peramalan beban, dan AI agent untuk operasional kelistrikan.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


def initialize_data_sources() -> None:
    global FEEDERS, INCIDENTS, FORECAST_POINTS, FEEDER_MAP, TOTAL_CUSTOMERS, DATA_SOURCE

    sources = {"feeder": "default", "incident": "default", "forecast": "default"}
    errors: list[str] = []

    feeder_file = DATA_DIR / "feeder_master.csv"
    incident_file = DATA_DIR / "incidents.csv"
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
        "counts": {
            "feeder": len(FEEDERS),
            "incident": len(INCIDENTS),
            "forecast_points": len(FORECAST_POINTS),
        },
    }


initialize_data_sources()


class AgentRequest(BaseModel):
    message: str


class AgentResponse(BaseModel):
    answer: str
    source: str


def compute_keandalan():
    sum_rn = 0
    for event in INCIDENTS:
        cust = FEEDER_MAP[event["feeder"]]["customers"]
        sum_rn += event["duration"] * cust

    saidi_min = sum_rn / TOTAL_CUSTOMERS
    saidi_h = saidi_min / 60
    saifi = sum(FEEDER_MAP[event["feeder"]]["customers"] for event in INCIDENTS) / TOTAL_CUSTOMERS
    caidi_min = saidi_min / saifi if saifi else 0
    caidi_h = caidi_min / 60

    per_feeder = []
    for feeder in FEEDERS:
        events = [event for event in INCIDENTS if event["feeder"] == feeder["id"]]
        total_duration = sum(event["duration"] for event in events)
        count = len(events)
        per_feeder.append(
            {
                "id": feeder["id"],
                "name": feeder["name"],
                "customers": feeder["customers"],
                "count": count,
                "sumR": total_duration,
                "saidiH": total_duration / 60,
                "saifi": count,
                "caidiH": (total_duration / count / 60) if count else 0,
            }
        )

    monthly = []
    for i, month_name in enumerate(MONTHS):
        events = [event for event in INCIDENTS if event["month"] == i]
        m_rn = sum(event["duration"] * FEEDER_MAP[event["feeder"]]["customers"] for event in events)
        m_n = sum(FEEDER_MAP[event["feeder"]]["customers"] for event in events)
        monthly.append(
            {
                "bulan": month_name,
                "saidi": round((m_rn / TOTAL_CUSTOMERS), 2),
                "saifi": round((m_n / TOTAL_CUSTOMERS), 3),
                "kejadian": len(events),
            }
        )

    return {
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


def compute_forecast():
    prediksi = [*FORECAST_POINTS]
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
        "summary": {
            "peak_mw": peak_mw,
            "peak_hour": peak_point["hour"],
            "off_peak_mw": round(off_peak_point["beban_mw"], 1),
            "off_peak_hour": off_peak_point["hour"],
            "average_mw": round(avg_mw, 1),
            "status": status,
            "model": "CSV Input" if DATA_SOURCE["sources"]["forecast"] != "default" else "MLPRegressor",
        },
    }


def generate_fallback_agent_answer(message: str) -> str:
    lower = message.lower()

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
def ml_forecast() -> dict[str, Any]:
    return compute_forecast()


AGENT_SYSTEM_PROMPT = (
    "Anda adalah asisten AI pada sistem terintegrasi PLN UP2D Balikpapan "
    "(peramalan beban listrik jangka pendek + indeks keandalan jaringan SAIDI/SAIFI/CAIDI).\n\n"
    "Aturan wajib:\n"
    "1. Untuk pertanyaan tentang prediksi/beban, WAJIB panggil tool get_prediksi_beban. "
    "Untuk pertanyaan tentang SAIDI/SAIFI/CAIDI/penyulang/tren gangguan, WAJIB panggil tool get_ringkasan_keandalan. "
    "JANGAN PERNAH mengarang angka dari ingatan.\n"
    "2. Ingatkan singkat bahwa data bersifat contoh/simulasi (bukan data SCADA real-time) saat pertama kali "
    "menyebut angka spesifik dalam sesi.\n"
    "3. Anda hanya memberi analisis/rekomendasi (decision-support) — jangan pernah memerintahkan tindakan "
    "operasional (switching, pemadaman, dsb).\n"
    "4. Jawab dalam Bahasa Indonesia, ringkas (maksimal ~4 kalimat), sertakan satuan yang tepat."
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
                "Mengambil prediksi beban listrik 24 jam ke depan: titik beban puncak, rata-rata, beban "
                "terendah (off-peak), dan status (NORMAL/SIAGA/AWAS)."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def _execute_agent_tool(name: str) -> dict[str, Any]:
    if name == "get_ringkasan_keandalan":
        return compute_keandalan()
    if name == "get_prediksi_beban":
        return compute_forecast()
    return {"error": f"tool tidak dikenal: {name}"}


@app.post("/api/agent/chat", response_model=AgentResponse)
async def agent_chat(payload: AgentRequest) -> AgentResponse:
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()

    if Groq is None or not groq_api_key or "tempel_api_key" in groq_api_key:
        return AgentResponse(answer=generate_fallback_agent_answer(payload.message), source="fallback")

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip() or "llama-3.3-70b-versatile"

    try:
        client = Groq(api_key=groq_api_key)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": payload.message},
        ]

        for _ in range(4):
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
                    result = _execute_agent_tool(tc.function.name)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})
                continue

            answer = (msg.content or "").strip() or generate_fallback_agent_answer(payload.message)
            return AgentResponse(answer=answer, source=f"groq:{model}")

        return AgentResponse(answer=generate_fallback_agent_answer(payload.message), source="fallback")
    except Exception as exc:  # pragma: no cover
        return AgentResponse(
            answer=f"Groq gagal dipanggil: {exc}. {generate_fallback_agent_answer(payload.message)}",
            source="fallback",
        )


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "PLN UP2D Balikpapan Integrated System API is running."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

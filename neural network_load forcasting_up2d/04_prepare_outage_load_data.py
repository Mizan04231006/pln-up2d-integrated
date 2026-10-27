"""
04_prepare_outage_load_data.py
Menyiapkan data forecasting beban padam dari rekap CSV mentah.

CSV sumber hanya berisi jumlah kejadian padam per tanggal. CSV tersebut tidak
memuat waktu kejadian, durasi, atau MW yang terputus. Karena itu keluaran
memisahkan nilai observasi dan estimasi:

  - Oktober: jumlah kejadian harian dibaca langsung dari baris TOTAL UMUM + CAPTIVE.
  - Bulan lain: jumlah kejadian diperkirakan dari rata-rata pola Oktober.
  - MW padam: jumlah kejadian x MW rata-rata per kejadian, lalu dialokasikan
    mengikuti profil beban normal pada jam tersebut.

Keluaran:
  backend/data/data_beban_padam_up2d.csv       data hourly kompatibel MLP
  backend/data/rekap_beban_padam_harian.csv    audit agregasi harian
  backend/data/rekap_beban_padam_feeder.csv    audit per feeder dan kategori

Jalankan dari root repository:
  .venv\\Scripts\\python.exe "neural network_load forcasting_up2d\\04_prepare_outage_load_data.py"
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_FILE = ROOT_DIR / "backend" / "data" / "Data mentah untuk Load Forecasting dan SAIDI SAIFI CAIDI.csv"
NORMAL_LOAD_FILE = ROOT_DIR / "backend" / "data" / "data_beban_up2d.csv"
OUTPUT_DIR = ROOT_DIR / "backend" / "data"

START_DATE = "2022-01-01"
END_DATE = "2023-12-31 23:00:00"
AVERAGE_MW_PER_EVENT = 0.35
MAX_OUTAGE_SHARE = 0.45
RANDOM_SEED = 42


def _number(value: str) -> float:
    try:
        return float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return 0.0


def _read_raw_sections() -> tuple[
    list[str], list[float], dict[str, list[float]], dict[str, list[float]]
]:
    with SOURCE_FILE.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    total_header_index = next(
        index
        for index, row in enumerate(rows)
        if row and row[0].strip().upper() == "TOTAL UMUM + CAPTIVE"
    )
    total_row = rows[total_header_index + 1]
    date_labels = [cell.strip() for cell in rows[total_header_index][2:33]]
    total_counts = [_number(cell) for cell in total_row[2:33]]

    def read_section(header_text: str, end_index: int) -> dict[str, list[float]]:
        header_index = next(
            index
            for index, row in enumerate(rows[:end_index])
            if any(cell.strip().upper() == header_text for cell in row)
        )
        result: dict[str, list[float]] = {}
        for row in rows[header_index + 1 : end_index]:
            if len(row) < 33:
                continue
            feeder = row[0].strip()
            if not feeder or feeder.upper() in {"FEDEER", "PLG CAPTIVE"}:
                continue
            result[feeder] = [_number(cell) for cell in row[2:33]]
        return result

    general = read_section("PELANGGAN UMUM", total_header_index)
    captive_header_index = next(
        index
        for index, row in enumerate(rows[:total_header_index])
        if any(cell.strip().upper() == "PELANGGAN CAPTIVE" for cell in row)
    )
    captive = read_section("PELANGGAN CAPTIVE", total_header_index)
    if len(date_labels) != 31 or len(total_counts) != 31:
        raise ValueError("CSV mentah harus memiliki 31 kolom tanggal Oktober.")
    return date_labels, total_counts, general, captive


def _load_normal_load() -> pd.DataFrame:
    if NORMAL_LOAD_FILE.exists():
        frame = pd.read_csv(NORMAL_LOAD_FILE, parse_dates=["Waktu"])
        required = {"Waktu", "Beban_MW", "Suhu_C"}
        if required.issubset(frame.columns) and not frame.empty:
            return frame[["Waktu", "Beban_MW", "Suhu_C"]].rename(
                columns={"Beban_MW": "Beban_Normal_MW"}
            )

    dates = pd.date_range(START_DATE, END_DATE, freq="h")
    hour = dates.hour.to_numpy()
    base = 48 + 42 * np.exp(-((hour - 18) / 5) ** 2) + 10 * np.exp(-((hour - 10) / 4) ** 2)
    weekend_factor = np.where(dates.dayofweek.to_numpy() >= 5, 0.9, 1.0)
    temperature = 29 - 4 * np.cos((hour - 14) / 24 * 2 * np.pi)
    return pd.DataFrame(
        {
            "Waktu": dates,
            "Beban_Normal_MW": np.round(base * weekend_factor, 2),
            "Suhu_C": np.round(temperature, 1),
        }
    )


def _estimated_event_count(day: pd.Timestamp, observed_counts: list[float]) -> tuple[float, str]:
    observed = observed_counts[day.day - 1]
    if day.month == 10:
        return observed, "observed_daily_count"

    mean_count = float(np.mean(observed_counts))
    seasonal_factor = 1.0 + 0.12 * math.sin((day.month - 1) / 12 * 2 * math.pi)
    weekday_factor = 0.92 if day.dayofweek >= 5 else 1.0
    return round(mean_count * seasonal_factor * weekday_factor, 3), "estimated_from_october_mean"


def _build_daily_summary(
    normal_load: pd.DataFrame, observed_counts: list[float]
) -> pd.DataFrame:
    days = pd.date_range(normal_load["Waktu"].min().normalize(), normal_load["Waktu"].max().normalize(), freq="D")
    rows = []
    for day in days:
        count, count_source = _estimated_event_count(day, observed_counts)
        normal_day = normal_load[normal_load["Waktu"].dt.normalize() == day]
        normal_peak = float(normal_day["Beban_Normal_MW"].max())
        normal_average = float(normal_day["Beban_Normal_MW"].mean())
        estimated_shed = min(count * AVERAGE_MW_PER_EVENT, normal_peak * MAX_OUTAGE_SHARE)
        rows.append(
            {
                "Tanggal": day,
                "Kejadian_Padam": count,
                "Sumber_Jumlah_Kejadian": count_source,
                "Beban_Normal_Rata2_MW": round(normal_average, 3),
                "Beban_Normal_Puncak_MW": round(normal_peak, 3),
                "Beban_Padam_Harian_Estimasi_MW": round(estimated_shed, 3),
                "MW_Rata2_per_Kejadian_Asumsi": AVERAGE_MW_PER_EVENT,
                "Catatan": "Tidak ada durasi/MW terdampak pada sumber; nilai MW diestimasi.",
            }
        )
    return pd.DataFrame(rows)


def _build_hourly_data(normal_load: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    result = normal_load.copy()
    result["Tanggal"] = result["Waktu"].dt.normalize()
    result = result.merge(daily, on="Tanggal", how="left", validate="many_to_one")
    result["Jam"] = result["Waktu"].dt.hour
    result["Hari_Minggu"] = result["Waktu"].dt.dayofweek
    result["Bulan"] = result["Waktu"].dt.month
    result["Adalah_Libur"] = (result["Hari_Minggu"] >= 5).astype(int)

    daily_peak = result.groupby("Tanggal")["Beban_Normal_MW"].transform("max")
    profile_weight = (result["Beban_Normal_MW"] / daily_peak).clip(lower=0.25)
    weight_sum = profile_weight.groupby(result["Tanggal"]).transform("sum")
    result["Beban_Padam_MW"] = (
        result["Beban_Padam_Harian_Estimasi_MW"] * profile_weight / weight_sum
    ).round(3)

    # Beban_MW adalah target standar pipeline MLP dan sengaja berarti beban padam.
    result["Beban_MW"] = result["Beban_Padam_MW"]
    result["Suhu_C"] = result["Suhu_C"].round(1)
    result["Sumber_Data"] = np.where(
        result["Sumber_Jumlah_Kejadian"] == "observed_daily_count",
        "jumlah harian observasi; MW estimasi",
        "jumlah dan MW estimasi",
    )
    columns = [
        "Waktu",
        "Beban_MW",
        "Suhu_C",
        "Jam",
        "Hari_Minggu",
        "Bulan",
        "Adalah_Libur",
        "Beban_Normal_MW",
        "Beban_Padam_MW",
        "Kejadian_Padam",
        "Sumber_Data",
    ]
    return result[columns]


def _build_feeder_summary(
    general: dict[str, list[float]], captive: dict[str, list[float]]
) -> pd.DataFrame:
    rows = []
    for kategori, section in (("UMUM", general), ("CAPTIVE", captive)):
        for feeder, counts in section.items():
            rows.append(
                {
                    "Kategori": kategori,
                    "Pelanggan": feeder,
                    "Total_Kejadian_Oktober": int(sum(counts)),
                    "Hari_Aktif": int(sum(value > 0 for value in counts)),
                    "Kejadian_Maks_Harian": int(max(counts) if counts else 0),
                    "Sumber": "CSV mentah observasi",
                }
            )
    return pd.DataFrame(rows).sort_values(["Kategori", "Total_Kejadian_Oktober"], ascending=[True, False])


def main() -> None:
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"CSV sumber tidak ditemukan: {SOURCE_FILE}")

    np.random.seed(RANDOM_SEED)
    date_labels, total_counts, general, captive = _read_raw_sections()
    normal_load = _load_normal_load()
    daily = _build_daily_summary(normal_load, total_counts)
    hourly = _build_hourly_data(normal_load, daily)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    hourly.to_csv(OUTPUT_DIR / "data_beban_padam_up2d.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    daily.to_csv(OUTPUT_DIR / "rekap_beban_padam_harian.csv", index=False, date_format="%Y-%m-%d")
    _build_feeder_summary(general, captive).to_csv(
        OUTPUT_DIR / "rekap_beban_padam_feeder.csv", index=False
    )

    print(f"Sumber tanggal: {date_labels[0]} sampai {date_labels[-1]}")
    print(f"Data hourly: {len(hourly):,} baris")
    print(f"Data harian: {len(daily):,} baris")
    print(f"Rata-rata kejadian Oktober: {np.mean(total_counts):.2f} per hari")
    print(f"Rata-rata beban padam estimasi: {hourly['Beban_Padam_MW'].mean():.3f} MW")
    print("Output: backend/data/data_beban_padam_up2d.csv")


if __name__ == "__main__":
    main()

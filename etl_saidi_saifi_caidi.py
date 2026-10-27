"""
ETL rekap pemadaman mentah menjadi input SAIDI, SAIFI, dan CAIDI.

Sumber hanya mencatat hitungan gangguan feeder umum dan interupsi captive
harian untuk Oktober. Jumlah pelanggan feeder, durasi, serta tahun tidak ada.
Karena itu master dan durasi diestimasi secara eksplisit dan keluaran ditandai
sebagai estimasi, bukan data ukur.

Jalankan dari root repository:
  .venv\\Scripts\\python.exe etl_saidi_saifi_caidi.py

Output ditulis ke backend/data/saidi_saifi_feeder_master.csv dan
backend/data/saidi_saifi_incidents.csv.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "backend" / "data"
SOURCE_FILE = DATA_DIR / "Data mentah untuk Load Forecasting dan SAIDI SAIFI CAIDI.csv"

# Assumptions only for source fields that are absent.
ESTIMATED_CUSTOMERS_PER_FEEDER = 1000
ESTIMATED_DURATION_MINUTES = 60
MONTH_INDEX = 10
MONTH_LABEL = "Oktober"


def _read_number(value: str) -> int:
    try:
        return int(float(str(value).strip().replace(",", ".")))
    except (TypeError, ValueError):
        return 0


def _normalize_feeder(value: str) -> str:
    feeder = re.sub(r"\s+", "", (value or "").strip().upper())
    return feeder.lstrip("-")


def _read_source() -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    dict[str, list[int]],
    dict[str, list[int]],
    list[int],
]:
    with SOURCE_FILE.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    general_total_index = next(
        index for index, row in enumerate(rows)
        if row and row[0].strip().upper() == "TOTAL"
    )
    captive_marker_index = next(
        index for index, row in enumerate(rows)
        if any(cell.strip().upper() == "PELANGGAN CAPTIVE" for cell in row)
    )
    captive_header_index = captive_marker_index + 1
    overall_header_index = next(
        index for index, row in enumerate(rows)
        if row and row[0].strip().upper() == "TOTAL UMUM + CAPTIVE"
    )
    day_labels = rows[2][2:33]
    if len(day_labels) != 31:
        raise ValueError("CSV sumber harus memiliki 31 kolom tanggal Oktober.")

    general: dict[str, list[int]] = {}
    for row in rows[3:general_total_index]:
        if len(row) < 33 or not row[0].strip():
            continue
        feeder = _normalize_feeder(row[0])
        if feeder:
            general[feeder] = [_read_number(value) for value in row[2:33]]

    captive: dict[str, list[int]] = {}
    for row in rows[captive_header_index + 1 : overall_header_index]:
        if len(row) < 33 or not row[1].strip():
            continue
        feeder = _normalize_feeder(row[1])
        if not feeder:
            continue
        counts = [_read_number(value) for value in row[2:33]]
        if feeder not in captive:
            captive[feeder] = [0] * 31
        captive[feeder] = [left + right for left, right in zip(captive[feeder], counts)]

    overall_counts = [_read_number(value) for value in rows[overall_header_index + 1][2:33]]
    for day_index, overall in enumerate(overall_counts):
        reconciled = sum(counts[day_index] for counts in general.values()) + sum(
            counts[day_index] for counts in captive.values()
        )
        if reconciled != overall:
            raise ValueError(
                f"Total kejadian tanggal {day_index + 1} Oktober tidak cocok: "
                f"rekap feeder={reconciled}, baris total={overall}."
            )

    feeders = sorted(set(general) | set(captive))
    feeder_rows = [
        {
            "id": feeder,
            "name": feeder,
            "customers": ESTIMATED_CUSTOMERS_PER_FEEDER,
            "customers_estimated": True,
            "source": "estimasi tetap; jumlah pelanggan tidak tersedia di CSV",
        }
        for feeder in feeders
    ]

    events: list[dict[str, object]] = []
    event_id = 1
    for day_index in range(31):
        date_label = f"{day_index + 1} Okt"
        for feeder, counts in general.items():
            count = counts[day_index]
            if count <= 0:
                continue
            events.append(
                {
                    "id": event_id,
                    "month": MONTH_INDEX,
                    "date": date_label,
                    "time": "",
                    "feeder": feeder,
                    "duration": ESTIMATED_DURATION_MINUTES,
                    "cause": "Gangguan feeder (durasi estimasi)",
                    "method": "Tidak diketahui",
                    "event_count": count,
                    "affected_customers": count * ESTIMATED_CUSTOMERS_PER_FEEDER,
                    "category": "UMUM",
                    "duration_estimated": True,
                }
            )
            event_id += 1
        for feeder, counts in captive.items():
            count = counts[day_index]
            if count <= 0:
                continue
            events.append(
                {
                    "id": event_id,
                    "month": MONTH_INDEX,
                    "date": date_label,
                    "time": "",
                    "feeder": feeder,
                    "duration": ESTIMATED_DURATION_MINUTES,
                    "cause": "Interupsi captive (durasi estimasi)",
                    "method": "Tidak diketahui",
                    "event_count": count,
                    "affected_customers": count,
                    "category": "CAPTIVE",
                    "duration_estimated": True,
                }
            )
            event_id += 1

    return feeder_rows, events, general, captive, overall_counts


def main() -> None:
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"CSV sumber tidak ditemukan: {SOURCE_FILE}")

    feeder_rows, events, general, captive, daily_totals = _read_source()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    feeder_file = DATA_DIR / "saidi_saifi_feeder_master.csv"
    with feeder_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=feeder_rows[0].keys())
        writer.writeheader()
        writer.writerows(feeder_rows)

    incident_file = DATA_DIR / "saidi_saifi_incidents.csv"
    with incident_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=events[0].keys())
        writer.writeheader()
        writer.writerows(events)

    general_count = sum(sum(values) for values in general.values())
    captive_count = sum(sum(values) for values in captive.values())
    print(f"Feeder terdaftar: {len(set(general) | set(captive))}")
    print(f"Interupsi umum dari CSV: {general_count}")
    print(f"Interupsi captive dari CSV: {captive_count}")
    print(f"Total baris harian Oktober: {sum(daily_totals)}")
    print(f"Total pelanggan estimasi: {len(set(general) | set(captive)) * ESTIMATED_CUSTOMERS_PER_FEEDER}")
    print(f"Durasi estimasi per interupsi: {ESTIMATED_DURATION_MINUTES} menit")
    print(f"Output: {DATA_DIR / 'saidi_saifi_feeder_master.csv'}")
    print(f"Output: {DATA_DIR / 'saidi_saifi_incidents.csv'}")


if __name__ == "__main__":
    main()

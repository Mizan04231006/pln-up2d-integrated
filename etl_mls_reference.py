#!/usr/bin/env python3
"""
ETL referensi: JADWAL_PEMADAMAN_100_HARI.xlsx  ->  CSV bersih untuk backend/data/

Sumber (HANYA dua sheet ini yang dibaca):
  - DATABASE  : master penyulang (UP3, ULP, GI, jumlah pelanggan APKT, beban puncak)
  - REKAP MLS : kejadian pemadaman bergilir / Manual Load Shedding (MLS), 1 baris = 1 kejadian

Sheet lain (DATA BASE CAPTIVE, REALISASI CAPTIVE, kolom VVIP/LOKASI, NAMA JALAN) memuat
data pelanggan/lokasi dan SENGAJA tidak dibaca agar tidak ikut ke repo publik.

Kebutuhan:  pip install pandas openpyxl
Pemakaian:
    python etl_mls_reference.py --xlsx JADWAL_PEMADAMAN_100_HARI.xlsx --out ./etl_out

Keluaran di folder --out:
    mls_events.csv           kejadian bersih (tanpa nama pelanggan/lokasi)
    feeder_master.csv        master penyulang utama (id,name,customers,up3,ulp,gi,scope,bp_mw)
    data_quality_report.json hitungan baris yang dibuang/ditandai beserta alasannya
    golden_numbers.json      angka acuan SAIDI/SAIFI/CAIDI untuk menguji implementasi backend
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

ULP_ALIAS = {
    "GROGOT": "TANAH GROGOT",
    "SANGGATA": "SANGATTA",
    "SANGATA": "SANGATTA",
    "TJ REDEB": "TANJUNG REDEB",
    "SAMBOJA)": "SAMBOJA",
}


def norm_ulp(x) -> str | None:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    s = " ".join(str(x).upper().split())
    return ULP_ALIAS.get(s, s)


def to_minutes(v) -> float:
    """Jam (datetime.time / datetime) -> menit sejak 00:00; NaN bila kosong/bukan jam."""
    if isinstance(v, (dt.datetime, dt.time)):
        return v.hour * 60 + v.minute + v.second / 60
    return np.nan


def hhmm(minutes: float) -> str:
    if pd.isna(minutes):
        return ""
    m = int(round(minutes)) % 1440
    return f"{m // 60:02d}:{m % 60:02d}"


def load_master(xlsx: Path) -> pd.DataFrame:
    db = pd.read_excel(xlsx, sheet_name="DATABASE", header=1).dropna(subset=["FEEDER"]).copy()
    db["FEEDER"] = db["FEEDER"].astype(str).str.strip().str.upper()
    # Baris bernama ber-spasi (mis. "IND.01 LBS Telkom ...") = sub-bagian LBS/Recloser, BUKAN penyulang.
    main = db[~db["FEEDER"].str.contains(r"\s", regex=True)].copy()
    main["customers"] = pd.to_numeric(main["JUMLAH PELANGGAN APKT"], errors="coerce")
    main["bp_mw"] = pd.to_numeric(main["BP (MW)"], errors="coerce")
    out = pd.DataFrame(
        {
            "id": main["FEEDER"],
            "name": main["FEEDER"],
            "customers": main["customers"],
            "up3": main["UP3"].astype(str).str.strip().str.upper(),
            "ulp": main["ULP"].map(norm_ulp),
            "gi": main["NAMA GI"].fillna("").astype(str).str.strip(),
            "scope": main["KALTIMRA / ISOLATED"].astype(str).str.strip().str.upper(),
            "bp_mw": main["bp_mw"],
        }
    )
    out = out.sort_values("customers", ascending=False).drop_duplicates("id", keep="first")
    return out.sort_values("id").reset_index(drop=True)


def load_events(xlsx: Path, master: pd.DataFrame) -> pd.DataFrame:
    ev = pd.read_excel(xlsx, sheet_name="REKAP MLS", header=0)
    ev["TANGGAL"] = pd.to_datetime(ev["TANGGAL"], errors="coerce")
    ev = ev.dropna(subset=["TANGGAL"]).copy()
    ev["feeder"] = ev["FEDEER"].astype(str).str.strip().str.upper()  # (sic) header asli salah ketik "FEDEER"

    off_m = ev["WAKTU OFF"].map(to_minutes)
    on_m = ev["WAKTU ON"].map(to_minutes)
    delta = on_m - off_m
    delta = np.where(delta < 0, delta + 1440, delta)  # melewati tengah malam
    duration_min = np.where(on_m.isna(), np.nan, np.round(delta, 1))

    plg = pd.to_numeric(ev["PLG"], errors="coerce")
    m = ev[["feeder"]].merge(master[["id", "customers", "up3", "ulp", "scope"]], left_on="feeder", right_on="id", how="left")
    in_master = m["id"].notna().to_numpy()
    master_cust = m["customers"].to_numpy()

    cust = np.where(plg.notna(), plg, master_cust)
    cust_src = np.where(plg.notna(), "PLG", np.where(~np.isnan(master_cust), "master", "none"))
    # Ni efektif: jumlah pelanggan padam tidak boleh melebihi total pelanggan penyulang di master.
    # (71 baris PLG > master; tanpa pembatasan SAIDI penyulang bisa tembus ratusan jam.)
    cust_eff = np.where(~np.isnan(master_cust), np.minimum(cust, master_cust), cust)

    kategori = ev["KATEGORI"].fillna("TIDAK_DIKETAHUI").astype(str).str.strip().str.upper()
    flags = []
    for i in range(len(ev)):
        f = []
        if np.isnan(duration_min[i]):
            f.append("tanpa_waktu_on")
        if not np.isnan(duration_min[i]) and duration_min[i] > 720:
            f.append("durasi_ekstrem")  # > 12 jam: kemungkinan salah ketik jam; TETAP dihitung, hanya ditandai
        if cust_src[i] == "master":
            f.append("pelanggan_dari_master")
        if cust_src[i] == "none":
            f.append("pelanggan_tidak_ada")
        if not in_master[i]:
            f.append("feeder_tidak_di_master")
        if in_master[i] and np.isnan(master_cust[i]):
            f.append("master_tanpa_pelanggan")
        if plg.iloc[i] == plg.iloc[i] and in_master[i] and not np.isnan(master_cust[i]) and plg.iloc[i] > master_cust[i]:
            f.append("plg_melebihi_master")
        flags.append("|".join(f))

    out = pd.DataFrame(
        {
            "date": ev["TANGGAL"].dt.strftime("%Y-%m-%d").to_numpy(),
            "time_off": [hhmm(x) for x in off_m],
            "time_on": [hhmm(x) for x in on_m],
            "duration_min": duration_min,
            "feeder": ev["feeder"].to_numpy(),
            "up3": m["up3"].to_numpy(),
            "ulp": m["ulp"].to_numpy(),
            "kategori": kategori.to_numpy(),
            "customers_affected": cust,
            "customers_effective": cust_eff,
            "customers_src": cust_src,
            "load_mw": pd.to_numeric(ev["BEBAN OFF (MW)"], errors="coerce").to_numpy(),
            "flags": flags,
            "in_master": in_master,
        }
    )
    out.insert(0, "id", np.arange(1, len(out) + 1))
    return out


def eligible(events: pd.DataFrame) -> pd.DataFrame:
    """Aturan baku SAIDI/SAIFI: pelanggan UMUM, feeder ada di master DAN jumlah pelanggannya diketahui
    (supaya pembilang dan penyebut mencakup populasi yang sama), durasi terverifikasi, Ni tersedia."""
    return events[
        (events["kategori"] == "UMUM")
        & events["in_master"]
        & ~events["flags"].str.contains("master_tanpa_pelanggan")
        & events["duration_min"].notna()
        & events["customers_effective"].notna()
    ]


def indices(d: pd.DataFrame, n_total: float) -> dict:
    saifi = d["customers_effective"].sum() / n_total
    saidi_h = (d["customers_effective"] * d["duration_min"] / 60).sum() / n_total
    saidi_uncapped = (d["customers_affected"] * d["duration_min"] / 60).sum() / n_total
    return {
        "n_events": int(len(d)),
        "n_customers_total": int(n_total),
        "saidi_h": round(float(saidi_h), 4),
        "saifi": round(float(saifi), 4),
        "caidi_h": round(float(saidi_h / saifi), 4) if saifi else None,
        "ens_mwh": round(float((d["load_mw"] * d["duration_min"] / 60).sum()), 1),
        "saidi_h_tanpa_pembatasan_ni": round(float(saidi_uncapped), 4),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--out", default="etl_out")
    ap.add_argument(
        "--anonymize",
        action="store_true",
        help="ganti kode penyulang & nama GI dengan alias (F001.., G01..); tabel alias disimpan di "
        "feeder_alias_PRIVATE.csv (JANGAN di-commit). Angka SAIDI/SAIFI tidak berubah.",
    )
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    master = load_master(Path(a.xlsx))
    events = load_events(Path(a.xlsx), master)
    ok = eligible(events)

    kal = master[(master["scope"] == "KALTIMRA") & master["customers"].notna()]
    nt_sys = kal["customers"].sum()
    assert nt_sys > 0 and len(ok) > 0, "master/events kosong - cek nama sheet & header"

    golden = {"periode": [events["date"].min(), events["date"].max()], "sistem_kaltimra_umum": indices(ok, nt_sys)}
    ok_tanpa_ekstrem = ok[~ok["flags"].str.contains("durasi_ekstrem")]
    golden["sistem_kaltimra_umum"]["saidi_h_tanpa_durasi_ekstrem"] = indices(ok_tanpa_ekstrem, nt_sys)["saidi_h"]
    golden["sistem_kaltimra_umum"]["hari_dengan_kejadian"] = int(ok["date"].nunique())
    golden["per_up3"] = {}
    for up3, g in kal.groupby("up3"):
        sub = ok[ok["up3"] == up3]
        if len(sub):
            golden["per_up3"][up3] = indices(sub, g["customers"].sum())
    golden["per_bulan"] = {}
    for ym, g in ok.assign(ym=pd.to_datetime(ok["date"]).dt.strftime("%Y-%m")).groupby("ym"):
        golden["per_bulan"][ym] = indices(g, nt_sys)

    quality = {
        "total_baris_rekap_mls": int(len(events)),
        "kategori": events["kategori"].value_counts().to_dict(),
        "baris_tanpa_waktu_on": int(events["duration_min"].isna().sum()),
        "baris_pelanggan_dari_master": int((events["customers_src"] == "master").sum()),
        "baris_pelanggan_tidak_ada": int((events["customers_src"] == "none").sum()),
        "baris_feeder_tidak_di_master": int((~events["in_master"]).sum()),
        "baris_durasi_ekstrem_lebih_12_jam": int(events["flags"].str.contains("durasi_ekstrem").sum()),
        "baris_duplikat_persis_semua": int(events.duplicated(["feeder", "date", "time_off", "time_on"], keep=False).sum()),
        "baris_duplikat_persis_di_populasi_baku": int(ok.duplicated(["feeder", "date", "time_off", "time_on"], keep=False).sum()),
        "baris_plg_melebihi_master": int(events["flags"].str.contains("plg_melebihi_master").sum()),
        "baris_penyulang_master_tanpa_pelanggan": int(events["flags"].str.contains("master_tanpa_pelanggan").sum()),
        "event_lolos_aturan_baku": int(len(ok)),
        "penyulang_master": int(len(master)),
        "penyulang_master_tanpa_pelanggan": int(master["customers"].isna().sum()),
    }

    events = events.drop(columns=["in_master"])
    if a.anonymize:
        ids = sorted(set(master["id"]) | set(events["feeder"]))
        f_alias = {fid: f"F{i + 1:03d}" for i, fid in enumerate(ids)}
        g_alias = {g: f"G{i + 1:02d}" for i, g in enumerate(sorted(master["gi"].dropna().unique()))}
        pd.DataFrame({"alias": list(f_alias.values()), "asli": list(f_alias.keys())}).to_csv(
            out / "feeder_alias_PRIVATE.csv", index=False
        )
        events["feeder"] = events["feeder"].map(f_alias)
        master = master.assign(id=master["id"].map(f_alias), name=master["id"].map(f_alias), gi=master["gi"].map(g_alias))
    events.to_csv(out / "mls_events.csv", index=False)
    master.to_csv(out / "feeder_master.csv", index=False)
    (out / "data_quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False))
    (out / "golden_numbers.json").write_text(json.dumps(golden, indent=2, ensure_ascii=False))
    print(json.dumps({"quality": quality, "golden_sistem": golden["sistem_kaltimra_umum"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

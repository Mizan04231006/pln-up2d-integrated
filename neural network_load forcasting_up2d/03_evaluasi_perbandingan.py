# =============================================================================
#  03_evaluasi_perbandingan.py
#  Perbandingan Setting 1 vs Setting 2 — sesuai RPS Tahap 10-15
#  Jalankan SETELAH 02_train_model.py dijalankan untuk KEDUA setting
# =============================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle
import os

from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error

# ── Muat data & scaler ────────────────────────────────────────────────────────
print("=" * 60)
print("  PERBANDINGAN SETTING — PLN UP2D BALIKPAPAN")
print("=" * 60)

for f in ["data_beban_up2d.csv", "scaler_beban.pkl", "scaler_fitur.pkl"]:
    if not os.path.exists(f):
        raise FileNotFoundError(
            f"\nFile '{f}' tidak ditemukan!\n"
            "Pastikan sudah menjalankan:\n"
            "  python 01_generate_data.py\n"
            "  python 02_train_model.py  (untuk kedua setting)"
        )

df = pd.read_csv("data_beban_up2d.csv", parse_dates=["Waktu"])
df = df.sort_values("Waktu").reset_index(drop=True)

with open("scaler_beban.pkl", "rb") as f: scaler_beban = pickle.load(f)
with open("scaler_fitur.pkl", "rb") as f: scaler_fitur = pickle.load(f)

FITUR_INPUT = ["Beban_MW", "Suhu_C", "Jam", "Hari_Minggu", "Bulan", "Adalah_Libur"]
W = 24

df_norm               = df.copy()
df_norm[["Beban_MW"]] = scaler_beban.transform(df[["Beban_MW"]])
df_norm[FITUR_INPUT]  = scaler_fitur.transform(df[FITUR_INPUT])

fitur_arr = df_norm[FITUR_INPUT].values
beban_arr  = df_norm["Beban_MW"].values

X_list, y_list = [], []
for i in range(W, len(df_norm)):
    X_list.append(fitur_arr[i - W : i].flatten())
    y_list.append(beban_arr[i])

X = np.array(X_list)
y = np.array(y_list)

split  = int(len(X) * 0.8)
X_test = X[split:]
y_test = y[split:]
y_test_mw = scaler_beban.inverse_transform(y_test.reshape(-1, 1)).flatten()

# ── Evaluasi satu model ───────────────────────────────────────────────────────
def evaluasi(nama_file, label):
    if not os.path.exists(nama_file):
        print(f"  [!] {nama_file} belum ada — jalankan 02_train_model.py untuk {label}")
        return None

    with open(nama_file, "rb") as f: model = pickle.load(f)

    y_pred_n  = model.predict(X_test)
    y_pred_mw = scaler_beban.inverse_transform(y_pred_n.reshape(-1, 1)).flatten()

    mape = mean_absolute_percentage_error(y_test_mw, y_pred_mw) * 100
    rmse = np.sqrt(mean_squared_error(y_test_mw, y_pred_mw))
    mae  = np.mean(np.abs(y_test_mw - y_pred_mw))
    r2   = 1 - (np.sum((y_test_mw - y_pred_mw) ** 2)
                / np.sum((y_test_mw - np.mean(y_test_mw)) ** 2))

    print(f"\n  {label}")
    print(f"    MAPE  : {mape:.4f} %")
    print(f"    RMSE  : {rmse:.4f} MW")
    print(f"    MAE   : {mae:.4f}  MW")
    print(f"    R²    : {r2:.6f}")

    return {"label": label, "mape": mape, "rmse": rmse,
            "mae": mae, "r2": r2, "y_pred": y_pred_mw}

# Definisi setting sesuai 02_train_model.py
DESKRIPSI = {
    "model_setting_1.pkl": "Setting 1 — (64,32)  ep≤300  lr=0.001  bs=32",
    "model_setting_2.pkl": "Setting 2 — (128,64,32)  ep≤500  lr=0.0005  bs=16",
}

hasil = []
for fname, label in DESKRIPSI.items():
    h = evaluasi(fname, label)
    if h:
        hasil.append(h)

if not hasil:
    print("\nTidak ada model. Jalankan 02_train_model.py untuk masing-masing setting.")
    exit()

# ── Tabel perbandingan ────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  TABEL PERBANDINGAN")
print("=" * 60)
header = f"  {'Metrik':<14}"
for h in hasil:
    label_pendek = h["label"].split("—")[0].strip()
    header += f" {label_pendek:>16}"
print(header)
print("-" * 60)

for key, nama in [("mape","MAPE (%)"), ("rmse","RMSE (MW)"),
                  ("mae","MAE (MW)"),  ("r2","R²")]:
    baris = f"  {nama:<14}"
    vals  = [h[key] for h in hasil]
    for i, h in enumerate(hasil):
        baris += f" {h[key]:>16.4f}"
    # Tandai yang terbaik
    if len(hasil) == 2:
        if key in ["mape","rmse","mae"]:
            best = "← lebih baik" if vals[0] < vals[1] else ""
            baris2= f"  {nama:<14}"
            for v in vals: baris2 += f" {v:>16.4f}"
    print(baris)
print("=" * 60)

# Kesimpulan otomatis
if len(hasil) == 2:
    print("\n  Kesimpulan perbandingan:")
    for key, nama, lebih_kecil_lebih_baik in [
        ("mape","MAPE (%)", True), ("rmse","RMSE (MW)", True),
        ("mae", "MAE (MW)", True), ("r2",  "R²",        False)
    ]:
        v1, v2 = hasil[0][key], hasil[1][key]
        if lebih_kecil_lebih_baik:
            pemenang = hasil[0]["label"] if v1 < v2 else hasil[1]["label"]
        else:
            pemenang = hasil[0]["label"] if v1 > v2 else hasil[1]["label"]
        pemenang_pendek = pemenang.split("—")[0].strip()
        print(f"    {nama:<12} → {pemenang_pendek} lebih baik ({v1:.4f} vs {v2:.4f})")

# ── Ekspor CSV ────────────────────────────────────────────────────────────────
rows = [{"Setting": h["label"].split("—")[0].strip(),
         "Deskripsi": h["label"].split("—")[1].strip() if "—" in h["label"] else "",
         "MAPE (%)": round(h["mape"], 4),
         "RMSE (MW)": round(h["rmse"], 4),
         "MAE (MW)":  round(h["mae"],  4),
         "R2":        round(h["r2"],   6)} for h in hasil]
pd.DataFrame(rows).to_csv("tabel_perbandingan.csv", index=False)
print("\n  Tabel disimpan ke: tabel_perbandingan.csv")

# ── Visualisasi perbandingan ──────────────────────────────────────────────────
n_col  = 1 + len(hasil)
fig, axes = plt.subplots(1, n_col, figsize=(6 * n_col, 5))
fig.suptitle("Perbandingan Setting — Peramalan Beban PLN UP2D Balikpapan",
             fontsize=12, fontweight="bold")

# Bar chart metrik
ax = axes[0]
metrik_nama = ["MAPE (%)", "RMSE (MW)", "MAE (MW)"]
metrik_key  = ["mape", "rmse", "mae"]
x     = np.arange(len(metrik_nama))
lebar = 0.35
warna = ["#185FA5", "#D85A30"]

for i, h in enumerate(hasil):
    vals   = [h[k] for k in metrik_key]
    offset = (i - (len(hasil) - 1) / 2) * lebar
    bars   = ax.bar(x + offset, vals, lebar,
                    label=h["label"].split("—")[0].strip(),
                    color=warna[i % len(warna)], alpha=0.85)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.01,
                f"{bar.get_height():.2f}",
                ha="center", va="bottom", fontsize=8)

ax.set_xticks(x)
ax.set_xticklabels(metrik_nama)
ax.set_title("Perbandingan Metrik Error")
ax.legend(fontsize=8)
ax.grid(True, axis="y", alpha=0.3)

# Aktual vs prediksi per setting
n_tampil = 168
for i, h in enumerate(hasil):
    ax = axes[i + 1]
    ax.plot(y_test_mw[:n_tampil],    label="Aktual",   color="#185FA5", linewidth=1.5)
    ax.plot(h["y_pred"][:n_tampil],  label="Prediksi", color=warna[i % len(warna)],
            linestyle="--", linewidth=1.5)
    label_pendek = h["label"].split("—")[0].strip()
    ax.set_title(f"{label_pendek}\nMAPE={h['mape']:.2f}%  R²={h['r2']:.4f}")
    ax.set_xlabel("Jam ke-")
    ax.set_ylabel("Beban (MW)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("perbandingan_setting.png", dpi=150, bbox_inches="tight")
print("  Grafik disimpan ke: perbandingan_setting.png")
plt.show()

print("\nSelesai! Semua output siap untuk laporan proyek.")

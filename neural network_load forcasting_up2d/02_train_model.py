# =============================================================================
#  02_train_model.py
#  Peramalan Beban Jangka Pendek — PLN UP2D Balikpapan
#  Neural Network (MLP) dengan scikit-learn — TANPA TensorFlow
#
#  Library yang dibutuhkan (semua sudah ada di pip standar):
#      pip install scikit-learn pandas matplotlib numpy
#
#  Jalankan SETELAH 01_generate_data.py
#  Output: model_setting_1.pkl  (atau setting_2.pkl)
# =============================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle
import os
import time

from sklearn.neural_network    import MLPRegressor
from sklearn.preprocessing     import MinMaxScaler
from sklearn.metrics           import mean_absolute_percentage_error, mean_squared_error

# ── 0. Pilih SETTING — ganti ini untuk variasi kondisi (RPS Tahap 10-12) ─────
#
#   Untuk Setting 1: jalankan file ini langsung (sudah default di bawah)
#   Untuk Setting 2: ganti komentar pada blok SETTING di bawah, lalu jalankan ulang

SETTING = {
    "nama"            : "Setting 1",
    "hidden_layers"   : (64, 32),        # arsitektur jaringan: 2 hidden layer
    "activation"      : "relu",           # fungsi aktivasi
    "max_iter"        : 300,              # maks epoch
    "learning_rate"   : 0.001,            # learning rate awal
    "batch_size"      : 32,               # ukuran mini-batch
    "alpha"           : 0.0001,           # regularisasi L2
}

# ── Untuk SETTING 2, hapus tanda # di bawah ini dan beri tanda # pada SETTING di atas:
# SETTING = {
#     "nama"            : "Setting 2",
#     "hidden_layers"   : (128, 64, 32),   # arsitektur lebih dalam
#     "activation"      : "relu",
#     "max_iter"        : 500,
#     "learning_rate"   : 0.0005,
#     "batch_size"      : 16,
#     "alpha"           : 0.001,
# }

print("=" * 60)
print(f"  PERAMALAN BEBAN NN — PLN UP2D BALIKPAPAN")
print(f"  {SETTING['nama']}")
print(f"  Library: scikit-learn MLPRegressor")
print("=" * 60)

# ── 1. Muat data ──────────────────────────────────────────────────────────────
if not os.path.exists("data_beban_up2d.csv"):
    raise FileNotFoundError(
        "\nFile data_beban_up2d.csv tidak ditemukan!\n"
        "Jalankan dulu: python 01_generate_data.py\n"
    )

df = pd.read_csv("data_beban_up2d.csv", parse_dates=["Waktu"])
df = df.sort_values("Waktu").reset_index(drop=True)

print(f"\n[1] Data dimuat: {len(df):,} baris")
print(f"    Periode: {df['Waktu'].min().date()} → {df['Waktu'].max().date()}")

# ── 2. Preprocessing ──────────────────────────────────────────────────────────
print("\n[2] Preprocessing...")

# Tangani missing value
for col in ["Beban_MW", "Suhu_C"]:
    n_miss = df[col].isna().sum()
    if n_miss > 0:
        df[col] = df[col].interpolate(method="linear")
        print(f"    Interpolasi {n_miss} missing value di '{col}'")

FITUR_INPUT = ["Beban_MW", "Suhu_C", "Jam", "Hari_Minggu", "Bulan", "Adalah_Libur"]

# Scaler terpisah: scaler_beban untuk denormalisasi hasil prediksi
scaler_beban = MinMaxScaler()
scaler_fitur = MinMaxScaler()

df_norm               = df.copy()
df_norm[["Beban_MW"]] = scaler_beban.fit_transform(df[["Beban_MW"]])
df_norm[FITUR_INPUT]  = scaler_fitur.fit_transform(df[FITUR_INPUT])

# Simpan scaler
with open("scaler_beban.pkl", "wb") as f: pickle.dump(scaler_beban, f)
with open("scaler_fitur.pkl", "wb") as f: pickle.dump(scaler_fitur, f)

print(f"    Fitur input  : {FITUR_INPUT}")
print(f"    Normalisasi  : Min-Max [0, 1]")
print(f"    Scaler disimpan: scaler_beban.pkl & scaler_fitur.pkl")

# ── 3. Susun window time-series (sliding window 24 jam) ───────────────────────
print("\n[3] Menyusun window time-series (window = 24 jam)...")
W = 24

fitur_arr = df_norm[FITUR_INPUT].values
beban_arr  = df_norm["Beban_MW"].values

X_list, y_list = [], []
for i in range(W, len(df_norm)):
    X_list.append(fitur_arr[i - W : i].flatten())   # 24 jam × 6 fitur = 144 input
    y_list.append(beban_arr[i])                       # target: 1 jam ke depan

X = np.array(X_list)
y = np.array(y_list)

print(f"    Shape X : {X.shape}  (sampel × input_flat)")
print(f"    Shape y : {y.shape}")

# ── 4. Split train / test — kronologis (BUKAN acak) ──────────────────────────
print("\n[4] Membagi dataset (80% training / 20% testing)...")
split   = int(len(X) * 0.8)
X_train = X[:split];  y_train = y[:split]
X_test  = X[split:];  y_test  = y[split:]

print(f"    Training : {len(X_train):,} sampel")
print(f"    Testing  : {len(X_test):,}  sampel")

# ── 5. Bangun & latih model Neural Network ────────────────────────────────────
print(f"\n[5] Membangun model MLPRegressor...")
print(f"    Arsitektur hidden layer : {SETTING['hidden_layers']}")
print(f"    Aktivasi                : {SETTING['activation']}")
print(f"    Learning rate           : {SETTING['learning_rate']}")
print(f"    Batch size              : {SETTING['batch_size']}")
print(f"    Maks iterasi            : {SETTING['max_iter']}")

model = MLPRegressor(
    hidden_layer_sizes = SETTING["hidden_layers"],
    activation         = SETTING["activation"],
    solver             = "adam",
    alpha              = SETTING["alpha"],       # regularisasi L2
    batch_size         = SETTING["batch_size"],
    learning_rate_init = SETTING["learning_rate"],
    max_iter           = SETTING["max_iter"],
    early_stopping     = True,                   # berhenti jika val loss tidak turun
    validation_fraction= 0.1,
    n_iter_no_change   = 20,                     # sabar 20 iterasi sebelum stop
    random_state       = 42,
    verbose            = False,
)

print(f"\n[6] Training dimulai (harap tunggu)...")
t_mulai = time.time()
model.fit(X_train, y_train)
t_selesai = time.time()

epoch_aktual = model.n_iter_
print(f"    Selesai dalam {t_selesai - t_mulai:.1f} detik")
print(f"    Epoch yang dijalankan  : {epoch_aktual}")
print(f"    Loss akhir (training)  : {model.loss_:.6f}")
print(f"    Loss akhir (validasi)  : {model.best_validation_score_:.6f}")

# ── 7. Evaluasi ───────────────────────────────────────────────────────────────
print("\n[7] Evaluasi pada data testing...")
y_pred_norm = model.predict(X_test)

# Denormalisasi ke satuan MW
y_test_mw = scaler_beban.inverse_transform(y_test.reshape(-1, 1)).flatten()
y_pred_mw = scaler_beban.inverse_transform(y_pred_norm.reshape(-1, 1)).flatten()

mape = mean_absolute_percentage_error(y_test_mw, y_pred_mw) * 100
rmse = np.sqrt(mean_squared_error(y_test_mw, y_pred_mw))
mae  = np.mean(np.abs(y_test_mw - y_pred_mw))
r2   = 1 - (np.sum((y_test_mw - y_pred_mw) ** 2)
             / np.sum((y_test_mw - np.mean(y_test_mw)) ** 2))

print("\n" + "=" * 60)
print(f"  HASIL EVALUASI — {SETTING['nama']}")
print("=" * 60)
print(f"  MAPE   : {mape:.4f} %")
print(f"  RMSE   : {rmse:.4f} MW")
print(f"  MAE    : {mae:.4f}  MW")
print(f"  R²     : {r2:.6f}")
print("=" * 60)
if mape < 5:
    print("  MAPE < 5% — Model cukup akurat untuk peramalan beban!")
else:
    print("  MAPE >= 5% — Coba tuning hyperparameter (Setting 2)")
print("=" * 60)

# Simpan metrik ke file teks agar mudah dibandingkan
nama_setting = SETTING["nama"].replace(" ", "_").lower()
with open(f"hasil_{nama_setting}.txt", "w") as f:
    f.write(f"Setting : {SETTING['nama']}\n")
    f.write(f"Arsitektur    : {SETTING['hidden_layers']}\n")
    f.write(f"Epoch aktual  : {epoch_aktual}\n")
    f.write(f"Learning rate : {SETTING['learning_rate']}\n")
    f.write(f"Batch size    : {SETTING['batch_size']}\n")
    f.write(f"MAPE  : {mape:.4f} %\n")
    f.write(f"RMSE  : {rmse:.4f} MW\n")
    f.write(f"MAE   : {mae:.4f} MW\n")
    f.write(f"R2    : {r2:.6f}\n")

# ── 8. Simpan model ───────────────────────────────────────────────────────────
nama_file = f"model_{nama_setting}.pkl"
with open(nama_file, "wb") as f: pickle.dump(model, f)
print(f"\n  Model disimpan ke: {nama_file}")

# ── 9. Visualisasi ────────────────────────────────────────────────────────────
print("\n[8] Membuat grafik...")

fig, axes = plt.subplots(2, 2, figsize=(14, 9))
fig.suptitle(
    f"Peramalan Beban Jangka Pendek — PLN UP2D Balikpapan\n{SETTING['nama']}  "
    f"|  Arsitektur {SETTING['hidden_layers']}  |  Epoch={epoch_aktual}",
    fontsize=12, fontweight="bold"
)

# Plot 1: Kurva loss
ax = axes[0, 0]
ax.plot(model.loss_curve_,       label="Loss Training", color="#185FA5", linewidth=1.5)
if hasattr(model, "validation_scores_"):
    loss_val = [-v for v in model.validation_scores_]
    ax.plot(loss_val, label="Loss Validasi", color="#D85A30",
            linestyle="--", linewidth=1.5)
ax.set_title("Kurva Loss Training")
ax.set_xlabel("Iterasi (Epoch)")
ax.set_ylabel("MSE Loss")
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 2: Aktual vs Prediksi — 1 minggu (168 jam)
ax = axes[0, 1]
n_tampil = 168
ax.plot(y_test_mw[:n_tampil],  label="Aktual",   color="#185FA5", linewidth=1.5)
ax.plot(y_pred_mw[:n_tampil],  label="Prediksi", color="#D85A30",
        linestyle="--", linewidth=1.5)
ax.set_title("Aktual vs Prediksi (168 jam pertama data testing)")
ax.set_xlabel("Jam ke-")
ax.set_ylabel("Beban (MW)")
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 3: Scatter aktual vs prediksi
ax = axes[1, 0]
ax.scatter(y_test_mw, y_pred_mw, alpha=0.25, s=5, color="#185FA5")
lim = [min(y_test_mw.min(), y_pred_mw.min()) - 2,
       max(y_test_mw.max(), y_pred_mw.max()) + 2]
ax.plot(lim, lim, "r--", linewidth=1.5, label="Ideal (y=x)")
ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_title(f"Scatter Aktual vs Prediksi  |  R² = {r2:.4f}")
ax.set_xlabel("Aktual (MW)")
ax.set_ylabel("Prediksi (MW)")
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 4: Distribusi error
ax = axes[1, 1]
error = y_pred_mw - y_test_mw
ax.hist(error, bins=60, color="#185FA5", alpha=0.75, edgecolor="white")
ax.axvline(0, color="red", linestyle="--", linewidth=1.5, label="Nol error")
ax.axvline( mae, color="#D85A30", linestyle=":", linewidth=1.2, label=f"+MAE ({mae:.2f} MW)")
ax.axvline(-mae, color="#D85A30", linestyle=":", linewidth=1.2, label=f"-MAE")
ax.set_title(f"Distribusi Error  |  MAPE={mape:.2f}%  RMSE={rmse:.2f} MW")
ax.set_xlabel("Error (MW)")
ax.set_ylabel("Frekuensi")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

plt.tight_layout()
nama_grafik = f"grafik_{nama_setting}.png"
plt.savefig(nama_grafik, dpi=150, bbox_inches="tight")
print(f"  Grafik disimpan ke: {nama_grafik}")
plt.show()

print(f"\nSelesai! Jalankan 03_evaluasi_perbandingan.py setelah kedua setting selesai.")

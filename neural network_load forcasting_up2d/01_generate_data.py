# =============================================================================
#  01_generate_data.py
#  Generator data simulasi beban PLN UP2D Balikpapan
#  Jalankan file ini PERTAMA untuk membuat data_beban_up2d.csv
# =============================================================================

import pandas as pd
import numpy as np

np.random.seed(42)

# ── Parameter ────────────────────────────────────────────────────────────────
MULAI   = "2022-01-01"
SELESAI = "2023-12-31"

# ── Buat indeks waktu per jam ─────────────────────────────────────────────────
waktu = pd.date_range(start=MULAI, end=SELESAI, freq="h")
n     = len(waktu)

# ── Profil beban harian (MW) — pola khas kota tropis ─────────────────────────
# Beban rendah dini hari, naik pagi, puncak sore-malam
def profil_harian(jam):
    if   0  <= jam < 5:   return 48 + jam * 1.0          # dini hari rendah
    elif 5  <= jam < 9:   return 53 + (jam - 5)  * 5.5   # naik pagi
    elif 9  <= jam < 12:  return 75 + (jam - 9)  * 1.5   # stabil siang
    elif 12 <= jam < 14:  return 79 + (jam - 12) * 2.0   # puncak siang
    elif 14 <= jam < 17:  return 82                        # siang tinggi
    elif 17 <= jam < 21:  return 88 + (jam - 17) * 1.5   # puncak malam
    else:                 return 93 - (jam - 21) * 10     # turun malam

beban_dasar = np.array([profil_harian(t.hour) for t in waktu])

# ── Pengaruh hari (Sabtu-Minggu beban -10%) ───────────────────────────────────
faktor_hari = np.where(waktu.dayofweek >= 5, 0.90, 1.00)

# ── Pengaruh musim / bulan (Ramadan & Lebaran beban sedikit berbeda) ──────────
def faktor_bulanan(bulan):
    peta = {1:1.00, 2:0.98, 3:0.97, 4:1.03, 5:1.05,
            6:1.04, 7:1.02, 8:1.01, 9:1.00, 10:0.99, 11:0.98, 12:1.01}
    return peta.get(bulan, 1.00)
faktor_bulan = np.array([faktor_bulanan(t.month) for t in waktu])

# ── Pengaruh suhu terhadap beban (AC dominan di Balikpapan) ──────────────────
# Suhu Balikpapan: 24–36 °C, rata-rata ~29 °C
def suhu_simulasi(jam, bulan):
    base    = 29 + np.sin((bulan - 4) / 12 * 2 * np.pi) * 2
    diurnal = -4 * np.cos((jam - 14) / 24 * 2 * np.pi)   # panas jam 14
    noise   = np.random.normal(0, 0.8)
    return round(base + diurnal + noise, 1)

suhu = np.array([suhu_simulasi(t.hour, t.month) for t in waktu])

# Setiap kenaikan 1 °C di atas 29 °C → +1.2 MW (efek AC)
delta_suhu   = np.clip(suhu - 29, 0, None)
pengaruh_ac  = delta_suhu * 1.2

# ── Tren tahunan (pertumbuhan ~4% / tahun) ────────────────────────────────────
tren = 1.0 + 0.04 * (waktu.year - 2022) + 0.02 * (waktu.month / 12)

# ── Noise acak ±2% ────────────────────────────────────────────────────────────
noise = np.random.normal(0, 0.02, n)

# ── Gabungkan semua faktor ────────────────────────────────────────────────────
beban = (beban_dasar * faktor_hari * faktor_bulan * tren
         + pengaruh_ac
         + beban_dasar * noise)
beban = np.clip(beban, 30, 130).round(2)

# ── Buat fitur tambahan ───────────────────────────────────────────────────────
adalah_libur   = (waktu.dayofweek >= 5).astype(int)
hari_minggu    = waktu.dayofweek          # 0=Senin … 6=Minggu
jam            = waktu.hour
bulan          = waktu.month

# ── Simpan ke CSV ─────────────────────────────────────────────────────────────
df = pd.DataFrame({
    "Waktu"        : waktu,
    "Beban_MW"     : beban,
    "Suhu_C"       : suhu,
    "Jam"          : jam,
    "Hari_Minggu"  : hari_minggu,
    "Bulan"        : bulan,
    "Adalah_Libur" : adalah_libur,
})

df.to_csv("data_beban_up2d.csv", index=False)

print("=" * 55)
print("  Data berhasil dibuat: data_beban_up2d.csv")
print("=" * 55)
print(f"  Total baris   : {len(df):,} jam")
print(f"  Rentang waktu : {df['Waktu'].min()} → {df['Waktu'].max()}")
print(f"  Beban min     : {df['Beban_MW'].min()} MW")
print(f"  Beban maks    : {df['Beban_MW'].max()} MW")
print(f"  Beban rata²   : {df['Beban_MW'].mean():.2f} MW")
print(f"  Suhu min/maks : {df['Suhu_C'].min()} / {df['Suhu_C'].max()} °C")
print("=" * 55)
print("\nLangkah berikutnya: jalankan  02_train_model.py")

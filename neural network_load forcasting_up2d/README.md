# Peramalan Beban Jangka Pendek — PLN UP2D Balikpapan
## Neural Network (MLP) — scikit-learn | TANPA TensorFlow

Proyek untuk Tugas Besar **Kecerdasan Buatan (TE201428)**
Program Studi Teknik Elektro — Institut Teknologi Kalimantan

---

## Install Library (cukup satu baris!)

```bash
pip install scikit-learn pandas matplotlib numpy
```

Tidak perlu TensorFlow. scikit-learn sudah termasuk MLPRegressor
yang setara untuk tugas peramalan ini.

---

## Urutan Menjalankan

```
01_generate_data.py   →   02_train_model.py (Setting 1)
                      →   02_train_model.py (Setting 2)   →   03_evaluasi_perbandingan.py
```

### Langkah 1 — Buat data simulasi
```bash
python 01_generate_data.py
```
Output: `data_beban_up2d.csv` (17.497 baris, 2 tahun data per jam)

### Langkah 2 — Training Setting 1
```bash
python 02_train_model.py
```
Output: `model_setting_1.pkl`, `grafik_setting_1.png`

### Langkah 3 — Training Setting 2
Buka `02_train_model.py`, cari bagian **SETTING** (baris 28-37).
Beri tanda `#` pada blok Setting 1, hapus tanda `#` pada blok Setting 2.
Simpan, lalu jalankan ulang:
```bash
python 02_train_model.py
```
Output: `model_setting_2.pkl`, `grafik_setting_2.png`

### Langkah 4 — Bandingkan kedua setting
```bash
python 03_evaluasi_perbandingan.py
```
Output: `perbandingan_setting.png`, `tabel_perbandingan.csv`

---

## Perbandingan Setting (untuk Laporan)

| Parameter       | Setting 1        | Setting 2           |
|----------------|------------------|---------------------|
| Hidden layer   | (64, 32)         | (128, 64, 32)       |
| Aktivasi       | ReLU             | ReLU                |
| Maks iterasi   | 300              | 500                 |
| Learning rate  | 0.001            | 0.0005              |
| Batch size     | 32               | 16                  |
| Regularisasi L2| 0.0001           | 0.001               |
| Optimizer      | Adam             | Adam                |

---

## Input & Output Model

**Input:** 24 jam terakhir × 6 fitur = 144 nilai
- Beban (MW), Suhu (°C), Jam, Hari minggu, Bulan, Status libur

**Output:** Prediksi beban 1 jam ke depan (MW)

---

## Metrik Evaluasi

| Metrik | Target |
|--------|--------|
| MAPE   | < 5%   |
| RMSE   | serendah mungkin |
| R²     | mendekati 1.0    |

---

## Jika Menggunakan Data Nyata UP2D

Ganti `data_beban_up2d.csv` dengan data asli dari SCADA.
Pastikan kolom CSV menggunakan nama:
`Waktu, Beban_MW, Suhu_C, Jam, Hari_Minggu, Bulan, Adalah_Libur`

Atau sesuaikan nama kolom di baris `FITUR_INPUT` pada `02_train_model.py`.

## Menyiapkan Data Beban Padam dari CSV Mentah

File `backend/data/Data mentah untuk Load Forecasting dan SAIDI SAIFI CAIDI.csv`
hanya berisi jumlah kejadian padam per feeder dan tanggal Oktober. File tersebut
tidak menyediakan waktu kejadian, durasi, atau nilai MW yang terputus. Jalankan:

```bash
python "04_prepare_outage_load_data.py"
```

Skrip ini menghasilkan:

- `backend/data/data_beban_padam_up2d.csv` — data hourly dengan format input MLP.
- `backend/data/rekap_beban_padam_harian.csv` — audit jumlah kejadian dan estimasi
  beban padam harian.
- `backend/data/rekap_beban_padam_feeder.csv` — rekap kejadian per feeder dan
  kategori umum/captive.

Interpretasi data:

- Jumlah kejadian pada Oktober adalah observasi dari baris `TOTAL UMUM + CAPTIVE`.
- Bulan selain Oktober diperkirakan dari rata-rata pola Oktober dengan faktor
  musiman dan faktor akhir pekan.
- `Beban_Padam_MW` diperkirakan dari `0,35 MW` per kejadian dan dibatasi maksimum
  `45%` dari beban normal harian.
- Karena sumber tidak mencatat jam kejadian, beban padam dialokasikan mengikuti
  profil beban normal pada hari tersebut.

Dengan demikian, hasil ini cocok untuk forecasting beban padam berbasis estimasi,
bukan pengganti data SCADA. Kolom `Sumber_Data` wajib dipertahankan agar hasil
observasi dan estimasi tidak tertukar dalam laporan.

## Training Model Beban Padam

Setelah menjalankan `04_prepare_outage_load_data.py`, latih dua konfigurasi
neural network dengan:

```bash
python "05_train_outage_model.py"
```

Model dilatih dari `data_beban_padam_up2d.csv` dengan window 24 jam dan split
kronologis 80% training / 20% testing. Hasilnya:

- `backend/model/outage_model_setting_1.pkl`
- `backend/model/outage_model_setting_2.pkl`
- `backend/model/outage_scaler_beban.pkl`
- `backend/model/outage_scaler_fitur.pkl`
- `backend/data/outage_model_evaluation.json`
- `backend/data/outage_model_comparison.csv`

Setting 1 dan Setting 2 memakai arsitektur yang sama dengan eksperimen model
sebelumnya. MAPE dihitung hanya untuk target beban padam non-zero karena nilai
padam nol membuat MAPE tidak bermakna.

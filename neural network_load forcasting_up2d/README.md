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

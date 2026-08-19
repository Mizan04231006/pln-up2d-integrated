# Backend PLN UP2D Balikpapan Integrated System

## Persiapan

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Menjalankan server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoint utama

- GET /api/health
- GET /api/dashboard/keandalan
- GET /api/ml/forecast
- POST /api/agent/chat
- GET /api/data/source
- POST /api/data/reload

> Isi API key Gemini di file .env sebelum menggunakan mode AI Gemini real.

## Pakai data asli tanpa ubah kode

Backend sekarang otomatis membaca file CSV pada folder `backend/data`.
Jika file tidak ada atau format salah, sistem akan fallback ke data contoh.

### 1) Siapkan file sumber

- `backend/data/feeder_master.csv`
- `backend/data/incidents.csv`
- `backend/data/forecast_hourly.csv`

Semua file template sudah disediakan dan bisa langsung Anda ganti isinya dengan data riil.

### 2) Format minimal

`feeder_master.csv`
- Kolom wajib: `id,name,customers`
- `id` harus unik (contoh: `KLD`)

`incidents.csv`
- Kolom wajib: `date,time,feeder,duration,cause,method`
- Kolom opsional: `id,month`
- `month` boleh format `1-12` atau `0-11` (jika kosong, default ke Januari)
- `method` akan dinormalisasi: `RC/Remote/SCADA` menjadi `RC`, sisanya menjadi `Manual`

`forecast_hourly.csv`
- Kolom wajib: `hour,beban_mw`
- Umumnya 24 baris untuk 24 jam, tetapi boleh lebih/kurang sesuai kebutuhan analisis

### 3) Reload data

Setelah mengganti CSV, lakukan salah satu:

- restart backend, atau
- panggil `POST /api/data/reload`

Untuk cek backend sedang memakai data dari file atau fallback, panggil `GET /api/data/source`.

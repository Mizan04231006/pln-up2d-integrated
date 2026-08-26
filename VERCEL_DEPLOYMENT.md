# Deployment PLN UP2D Balikpapan Integrated System ke Vercel

Dokumen ini menjelaskan arsitektur deployment, environment variable, serta langkah
deploy ke Vercel. Frontend (Vite + React) dan backend (FastAPI) berada dalam **satu
Vercel project** dan **satu domain** (same-origin), sehingga frontend memanggil API
melalui path relatif `/api/...` — **tidak bergantung pada `localhost`**.

## Arsitektur

```
GitHub repo (pln-up2d-integrated)
        |
        v
      Vercel (1 project, 1 domain)
        |
        +--------------------------+
        |                          |
        v                          v
  Service "frontend"          Service "backend"
  root: frontend/             root: backend/
  (Vite + React build)        entrypoint: main:app  (FastAPI)
        |                          |
        +------ rewards /api/* ----+
                     |
                /api/agent/chat
                /api/ml/forecast
                /api/dashboard/keandalan
                /api/health
                /api/data/source
                /api/data/reload
```

- `vercel.json` mendefinisikan dua **service** (fitur **Services**, beta, tersedia di
  semua plan) — pendekatan yang direkomendasikan Vercel untuk repo berbahasa campuran
  (JS frontend + Python backend) dalam satu project.
- Rewrite `"/api/(.*)"` → service `backend`; Vercel meneruskan **path asli** (mis.
  `/api/agent/chat` tiba di FastAPI sebagai `/api/agent/chat`), sehingga seluruh route
  FastAPI yang sudah ada tetap berlaku tanpa perubahan.
- Rewrite `"/(.*)"` → service `frontend` untuk asset dashboard.

### Backend di Vercel
Backend berjalan sebagai **Python ASGI function** (runtime Python 3.12, dipatok lewat
`backend/.python-version`). `entrypoint: "main:app"` mengekspos objek `app` dari
`backend/main.py` — **source of truth backend tidak dipindah/ditulis ulang**.

File yang ikut ter-deploy untuk service backend (root `backend/`):
- `main.py` (seluruh logic)
- `requirements.txt` (dependency FastAPI, pydantic, groq, scikit-learn, dll.)
- `model/*.pkl` → model ML forecasting
- `data/*.csv` → feeder_master, incidents, forecast_hourly, dan **data_beban_up2d.csv**
  (salinan CSV historis yang dipakai model ML; diletakkan di `backend/data/` agar ikut
  deploy — `_load_historical_rows()` memprioritaskan `backend/data/data_beban_up2d.csv`)

## Environment Variable (wajib diset di Vercel)

> **JANGAN commit `.env` / API key ke Git.** `.env*` sudah di-`.vercelignore` & `.gitignore`.

| Variable          | Diperlukan | Nilai contoh (bukan secret)                         |
|-------------------|-----------|-------------------------------------------------------|
| `GROQ_API_KEY`    | Ya        | (secret Anda dari console.groq.com)                   |
| `GROQ_MODEL`      | Opsional  | `openai/gpt-oss-120b` (default jika kosong: `llama-3.3-70b-versatile`) |
| `CORS_ALLOW_ORIGINS` | Opsional | `http://localhost:5173,http://127.0.0.1:5173` (default) |

Cara set: Vercel > Project > Settings > Environment Variables > tambahkan untuk
Production/Preview/Development. Di Vercel, env project dibagikan ke seluruh service.

Catatan CORS: karena frontend & API **satu origin** di production, permintaan
antar-origin tidak terjadi sehingga CORS tidak perlu mengizinkan domain Vercel.
Nilai default hanya untuk development lokal (`localhost:5173`).

## Development Lokal (tetap berfungsi)

```bash
# Terminal 1 — backend
cd backend
..\.venv\Scripts\python -m uvicorn main:app --reload        # port 8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev                                                 # port 5173
```

Frontend memanggil `/api/...` relatif; Vite mem-proxy `/api` → `http://127.0.0.1:8000`
(lihat `frontend/vite.config.js`). Tidak perlu menyetel `VITE_API_BASE`.

`VITE_API_BASE` hanya diisi bila API sengaja dipisah di URL lain (tidak disarankan).

## Langkah Deploy

Vercel CLI **tidak perlu** — bisa deploy langsung dari Git:

1. Push perubahan ke GitHub (`git push origin main`).
2. Import repo di [vercel.com/new](https://vercel.com/new) (repo `Mizan04231006/pln-up2d-integrated`).
3. Vercel membaca `vercel.json` (Services) → otomatis build service `frontend` (Vite)
   dan `backend` (Python 3.12 + FastAPI).
4. Set env vars `GROQ_API_KEY` (wajib), `GROQ_MODEL`, `CORS_ALLOW_ORIGINS` di Project Settings.
5. Deploy. URL publik: `https://<project>.vercel.app`.
6. Smoke test endpoint:
   - `GET https://<project>.vercel.app/api/health`
   - `GET https://<project>.vercel.app/api/dashboard/keandalan`
   - `GET https://<project>.vercel.app/api/ml/forecast?horizon=24`
   - `POST https://<project>.vercel.app/api/agent/chat` body `{"message":"Siapa developer proyek ini?"}`

### Vercel CLI (opsional, untuk `vercel dev`)
```bash
npm i -g vercel
vercel link          # login & link ke project (ikuti prompt)
vercel dev           # jalankan frontend + backend Services secara lokal
```

## Limitation & Caveat

- **Scalability ML:** `scikit-learn` + `numpy` besar (±100+ MB). Cold start function
  Python mungkin sepersekian-detik lebih lambat dari function ringan. Forecast/model
  di-load atau diprediksi per-request di fungsi; ukuran model kecil (model_setting_1.pkl
  ≈ 277 KB) sehingga aman untuk Hobby.
- **AI Agent**: `/api/agent/chat` memanggil Groq. Definitive time-out Vercel Function
  default diperhitungkan; jika panggilan Groq lambat, naikkan durasi function/service.
- **Filesystem**: Vercel readonly — semua data/model harus ikut deploy (sudah via
  `backend/data` & `backend/model`). Tidak ada penulisan file runtime.
- **Services adalah beta**: jika Vercel mengubah perilaku Services, tinjau
  dokumentasi resmi. Alternatif (frontend + FastAPI terpisah) tidak disarankan karena
  memecah domain.
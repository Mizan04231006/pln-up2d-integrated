# Deployment: Semua di Vercel (frontend + backend, satu platform)

## Riwayat singkat (kenapa dokumen/setup berubah beberapa kali)

1. **Percobaan 1** — Vercel "Services" (beta, 1 project untuk frontend+backend).
   Gagal karena butuh toggle manual di dashboard yang tidak bisa dilakukan
   lewat file kode.
2. **Percobaan 2** — pisah ke Vercel (frontend) + Render (backend). Render
   ternyata kini meminta kartu kredit saat membuat Web Service untuk akun ini.
3. **Percobaan 3 (kode ini)** — SATU platform, satu project, satu domain,
   tanpa Services: **Vercel Python/FastAPI framework preset**. Vercel membuat
   satu serverless function Python dari entrypoint root `index.py` yang
   mengimpor `app` dari `backend/main.py`; FastAPI lalu melayani `/api/*`
   DAN build frontend React (`frontend/dist`) lewat middleware — sehingga
   frontend & backend berbagi satu origin.

> Kenapa bukan folder `api/` + `outputDirectory`? Mode static output
> (`buildCommand` + `outputDirectory`) membuat Vercel memperlakukan project
> sebagai situs statis murni dan TIDAK membuat function Python → `/api/*`
> mengembalikan 404 meski frontend tampil. Karena itu project ini memakai
> preset FastAPI dengan entrypoint root.

## Arsitektur

```
GitHub repo (root, satu Vercel project)
  ├── index.py            <- entrypoint ASGI Vercel: impor `app` + middleware
  │                          menyajikan frontend (frontend/dist), /api/* ke FastAPI
  ├── requirements.txt    <- dependency Python di ROOT (Vercel deteksi FastAPI)
  ├── backend/main.py     <- app FastAPI asli + seluruh endpoint (satu sumber kebenaran)
  ├── backend/data|model  <- CSV historis & artefak model ML (ikut ter-bundle)
  └── frontend/           <- React/Vite; buildCommand membangun ke frontend/dist

Satu domain:
  https://pln-up2d-integrated.vercel.app/            -> frontend (disajikan FastAPI)
  https://pln-up2d-integrated.vercel.app/api/...     -> FastAPI (health, keandalan,
                                                         ml/forecast, agent/chat)
```

## Yang penting di repo ini

- **`index.py` (root)** — satu-satunya entrypoint untuk Vercel. Mengimpor `app`
  dari `backend/main.py` apa adanya, lalu menambahkan middleware yang menyajikan
  build `frontend/dist` untuk path non-`/api` (dengan SPA fallback index.html).
  `/api/*`, `/docs`, `/redoc`, `/openapi.json` diteruskan ke FastAPI.
- **`requirements.txt` (root)** — salinan `backend/requirements.txt`. Wajib ada
  di root agar Vercel mendeteksi preset Python/FastAPI dan meng-install dependency.
- **`vercel.json`** — hanya `buildCommand` (build frontend). **Tanpa**
  `outputDirectory`, supaya Vercel membuat function Python, bukan situs statis.
- **`backend/main.py`** — loop tool-calling AI dikurangi 4 → 3 iterasi agar aman
  terhadap batas eksekusi 10 detik Vercel Hobby.
- Teruji lokal: `index.py` mengimpor `backend/main.py` (11 route); `/` menyajikan
  index.html, `/assets/*` terlayani, `/api/health` dan `/api/dashboard/keandalan`
  mengembalikan JSON 200.

## Batasan yang perlu diketahui (jujur)

- **Vercel Hobby (gratis)** membatasi setiap function maksimal ~10 detik eksekusi.
  - `/api/health`, `/api/dashboard/keandalan` — lokal, cepat, aman.
  - `/api/agent/chat` — panggil Groq 1–3x (tool calling); biasanya di bawah 10s,
    tapi bisa kena kalau jaringan lambat / banyak langkah tool.
  - Cold start Python (numpy + scikit-learn) paling terasa pada permintaan pertama;
    request berikutnya (warm) jauh lebih cepat.
- Data & model dibaca dari `backend/data` & `backend/model` (ikut ter-bundle).
  Forecast otomatis memakai fallback CSV bila model ML belum siap.

## Langkah deploy

1. Commit & push perubahan ini (root `index.py`, `requirements.txt`, `vercel.json`,
   `.vercelignore`, penghapusan `api/`).
2. Di Vercel dashboard, pastikan:
   - **Root Directory**: root repo `/` (bukan `frontend`/`backend`).
   - **Framework Preset**: biarkan Vercel auto-detect (harusnya **FastAPI** /
     Python) — JANGAN "Other" statis. Kalau menu ada, pilih FastAPI.
   - **Environment Variables**: `GROQ_API_KEY` dan
     `GROQ_MODEL=llama-3.3-70b-versatile`; hapus `VITE_API_BASE` (frontend
     memakai path relatif `/api/...`).
3. **Deployments → Redeploy** (atau otomatis oleh push GitHub).
4. Cek log build: harus ada build Python/FastAPI (bukan "no functions or
   static directory"), lalu `cd frontend && npm run build` selesai.
5. Uji:
   - `https://pln-up2d-integrated.vercel.app/api/health` → JSON `{"status":"ok",...}`
   - `https://pln-up2d-integrated.vercel.app/` → dashboard React
   - `https://pln-up2d-integrated.vercel.app/api/dashboard/keandalan` → JSON

## Kalau masih gagal / opsi lain

- `render.yaml` masih ada dari percobaan lama — tidak mengganggu Vercel,
  boleh dibiarkan atau dihapus.
- Kalau 504 sering terjadi di AI Agent, opsi lain: PythonAnywhere (gratis tanpa
  kartu kredit) — tapi cek dulu apakah tier gratisnya mengizinkan koneksi keluar
  ke api.groq.com sebelum pindah.

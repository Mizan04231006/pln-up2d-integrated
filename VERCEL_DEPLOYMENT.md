# Deployment: Semua di Vercel (frontend + backend, satu platform)

## Riwayat singkat (kenapa dokumen ini berubah lagi)

1. **Percobaan 1** — Vercel "Services" (beta, 1 project untuk frontend+backend).
   Gagal karena butuh toggle manual di dashboard yang tidak bisa dilakukan
   lewat file kode.
2. **Percobaan 2** — pisah ke Vercel (frontend) + Render (backend). Render
   ternyata sekarang meminta kartu kredit saat pembuatan Web Service baru untuk
   akun Anda — jadi tidak jadi dipakai.
3. **Percobaan 3 (dokumen ini)** — kembali ke SATU platform, tapi dengan cara
   yang benar: pakai **Vercel Python Serverless Functions** (fitur resmi,
   sudah lama stabil — beda dari fitur "Services" yang masih beta) lewat folder
   `api/` di root repo. Akun Vercel Anda yang sekarang sudah terbukti tidak
   perlu kartu kredit dipakai ulang — tidak perlu daftar platform baru sama sekali.

```
GitHub repo (root)
  ├── api/index.py        <- Vercel mendeteksi ini otomatis sbg serverless function
  ├── backend/main.py     <- app FastAPI asli, diimpor apa adanya oleh api/index.py
  └── frontend/           <- dibangun jadi static site (buildCommand di vercel.json)

Satu domain Vercel Anda melayani KEDUANYA:
  https://pln-up2d-integrated.vercel.app/          -> frontend (static)
  https://pln-up2d-integrated.vercel.app/api/...   -> backend (serverless function)
```

Karena frontend dan backend sekarang satu domain yang sama, **tidak perlu lagi**
env var `VITE_API_BASE` yang kemarin diisi URL Render — kosongkan/hapus
variable itu di Vercel dashboard (Settings → Environment Variables), supaya
frontend kembali memakai path relatif `/api/...` seperti desain awalnya.

## Yang sudah saya siapkan di repo ini

- **`api/index.py`** — entry point serverless, cuma mengimpor `app` dari
  `backend/main.py` apa adanya (bukan duplikasi logika — satu sumber kebenaran
  tetap di `backend/main.py`, dijalankan lewat `uvicorn` untuk development
  lokal seperti biasa).
- **`api/requirements.txt`** — salinan dependency yang sama dengan
  `backend/requirements.txt`, dibutuhkan Vercel Python builder membaca
  requirements di direktori yang sama dengan function-nya.
- **`backend/main.py`** — loop tool-calling AI Agent dikurangi dari maksimal 4
  jadi 3 iterasi, untuk memperbesar margin aman terhadap **batas eksekusi 10
  detik** di Vercel Hobby (gratis) — lihat catatan di bawah.
- Sudah saya uji: `api/index.py` berhasil mengimpor `backend/main.py` tanpa
  error, seluruh endpoint (`/api/health`, `/api/dashboard/keandalan`,
  `/api/ml/forecast`, `/api/agent/chat`) terdaftar dengan benar.

## Batasan yang perlu Anda ketahui (jujur, bukan jaminan sempurna)

Vercel Hobby (gratis) membatasi **setiap serverless function maksimal 10 detik
eksekusi** sebelum dihentikan paksa (504). Untuk endpoint `/api/dashboard/keandalan`
dan `/api/ml/forecast` ini nyaris pasti aman (cuma hitung-hitungan lokal, tidak
memanggil API luar). Untuk `/api/agent/chat`, yang memanggil Groq 1-3 kali
berurutan (tool calling), Groq terkenal sangat cepat sehingga BIASANYA total
di bawah 10 detik — tapi ini bukan jaminan mutlak, terutama kalau ada jaringan
lambat atau butuh 3 langkah tool. Kalau Anda mengalami error 504 khusus di tab
AI Agent (fitur dashboard lain tetap normal), itu tandanya kena batas ini.

## Langkah deploy

1. Push perubahan ini ke GitHub (`api/`, `api/requirements.txt`,
   `backend/main.py` yang sudah diubah).
2. Di Vercel dashboard, pastikan **Environment Variables** berisi
   `GROQ_API_KEY` dan `GROQ_MODEL=llama-3.3-70b-versatile` (Settings →
   Environment Variables — sebelumnya ini cuma ada di `backend/.env` lokal,
   Vercel tidak baca file `.env` dari repo, harus diisi manual di dashboard).
   **Hapus** `VITE_API_BASE` kalau masih ada dari percobaan Render.
3. **Deployments** → Redeploy (atau otomatis ter-trigger oleh push GitHub baru).
4. Setelah selesai, cek log build — kali ini harus muncul konfirmasi Vercel
   mendeteksi function Python di `api/index.py`, BUKAN lagi peringatan "no
   functions or static directory".
5. Uji `https://pln-up2d-integrated.vercel.app/api/health` di browser -> harus
   muncul JSON, bukan 404.

## Kalau masih gagal / mau opsi lain

- `render.yaml` masih ada di repo dari percobaan sebelumnya — tidak mengganggu
  apa pun kalau dibiarkan (Vercel tidak membacanya), boleh dihapus untuk
  kerapian atau dibiarkan kalau suatu saat Render tersedia lagi tanpa kartu
  kredit untuk akun Anda.
- Kalau error 504 di AI Agent benar-benar sering terjadi, opsi lain adalah
  PythonAnywhere (tier gratis, tanpa kartu kredit dikonfirmasi banyak sumber) —
  TAPI saya belum bisa memastikan apakah tier gratisnya mengizinkan koneksi
  keluar ke api.groq.com atau dibatasi ke daftar domain tertentu. Cek dulu hal
  ini sebelum pindah ke sana, supaya tidak buang waktu setup untuk hal yang
  ternyata tidak bisa jalan.

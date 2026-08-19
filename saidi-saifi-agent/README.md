# Evaluasi Keandalan Jaringan Distribusi (SAIDI/SAIFI/CAIDI) + Asisten AI

Proyek konversi mata kuliah **Sistem Distribusi Tenaga Listrik (TE2515020)**, Institut
Teknologi Kalimantan — dari hasil magang mandiri di PLN UP2D KALTIMRA.

Dashboard menghitung dan memvisualisasikan indeks keandalan jaringan distribusi 20 kV
(SAIDI, SAIFI, CAIDI) dari log kejadian gangguan, membandingkannya dengan standar SPLN
dan IEEE Std 1366, dan dilengkapi **Asisten AI** (didukung Gemini) yang bisa menjawab
pertanyaan bahasa alami tentang data tersebut — dengan cara memanggil ulang fungsi
perhitungan yang sama persis dengan yang menghasilkan angka di dashboard, bukan menebak.

> **Keterkaitan dengan RPS TE2515020**: dashboard ini menyasar CPMK-5 (menganalisis
> jaringan sistem distribusi secara sistematis) dan bahan kajian *Analisis Feeder
> Distribusi*. Lapisan Asisten AI adalah nilai tambah rekayasa (tidak wajib dari RPS ini)
> yang menunjukkan penerapan *AI-assisted analysis* di atas hasil kerja teknik yang
> sesungguhnya — silakan sesuaikan penekanan laporan Anda sesuai arahan dosen pembimbing.

Seluruh data (`src/data.js`) adalah **data contoh (dummy)** — gantilah dengan data riil
hasil magang Anda sebelum dipakai sebagai bukti kerja final.

---

## 1. Yang Anda Butuhkan Sebelum Mulai

| Kebutuhan | Keterangan |
|---|---|
| **VS Code** | [code.visualstudio.com](https://code.visualstudio.com) |
| **Node.js versi 20 ke atas** | [nodejs.org](https://nodejs.org) — pilih versi **LTS**. Cek dengan `node -v` di terminal. |
| **API key Gemini (gratis)** | Lihat Langkah 4 di bawah. **Bukan** hal yang sama dengan langganan Gemini Pro/Advanced di aplikasi Gemini — lihat kotak penjelasan di Langkah 4. |

---

## 2. Buka Proyek di VS Code

1. Ekstrak (unzip) folder proyek ini ke lokasi mana pun di komputer Anda, misalnya `Documents/saidi-saifi-agent`.
2. Buka **VS Code** → menu **File → Open Folder…** → pilih folder `saidi-saifi-agent` hasil ekstrak.
3. Buka terminal bawaan VS Code: menu **Terminal → New Terminal** (atau `` Ctrl+` ``).

---

## 3. Instal Dependensi

Di terminal VS Code (pastikan Anda berada di folder proyek), jalankan:

```bash
npm install
```

Tunggu sampai selesai (biasanya 1-2 menit). Ini mengunduh React, Vite, Recharts, dan SDK Gemini (`@google/genai`).

---

## 4. Dapatkan API Key Gemini GRATIS

> **Penting — ini sering membingungkan:** langganan **Gemini Pro/Advanced untuk mahasiswa**
> (dari email kampus Anda) memberi Anda akses ke **aplikasi chat Gemini** dengan kuota lebih
> besar. Itu **terpisah** dari **Gemini Developer API** yang dipakai kode di proyek ini.
> Kabar baiknya: Gemini Developer API punya **tingkat gratis sendiri** yang bisa dipakai
> siapa saja dengan akun Google, **tanpa kartu kredit**, terlepas dari status langganan Anda.

Langkah mendapatkan API key:

1. Buka **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)** dan masuk dengan akun Google Anda (boleh akun kampus atau pribadi).
2. Klik **"Create API key"** (atau "Buat kunci API").
3. Salin key yang muncul (formatnya diawali `AIza...`).
4. Kembali ke VS Code. Di folder proyek, salin file **`.env.example`** menjadi file baru bernama **`.env`**:
   - Klik kanan `.env.example` di panel Explorer → **Copy** → klik kanan folder root → **Paste** → ganti nama hasil salinan menjadi `.env`.
   - Atau lewat terminal: `cp .env.example .env` (Mac/Linux) atau `copy .env.example .env` (Windows).
5. Buka file `.env`, ganti `tempel_api_key_gemini_anda_di_sini` dengan API key yang Anda salin tadi. Simpan (`Ctrl+S`).

Model yang dipakai proyek ini (`gemini-2.5-flash`) berada di tingkat gratis yang paling
longgar kuotanya — cukup untuk pemakaian pengujian/demo sehari-hari. Jika suatu saat Anda
melihat error "429" di chat, itu artinya kuota per-menit tercapai — tunggu sebentar lalu
coba lagi.

---

## 5. Jalankan Proyek

Di terminal VS Code:

```bash
npm run dev
```

Setelah muncul tulisan seperti `Local: http://localhost:5173/`, buka alamat tersebut di
browser (biasanya terbuka otomatis). Dashboard akan tampil dengan 5 tab: **Ringkasan**,
**Tren Bulanan**, **Per Penyulang**, **Data Mentah**, dan **Asisten AI**.

Buka tab **Asisten AI**, coba salah satu saran pertanyaan atau ketik pertanyaan sendiri,
misalnya:

- *"Penyulang mana yang paling buruk keandalannya?"*
- *"Berapa SAIDI dan SAIFI dibanding standar IEEE?"*
- *"Bulan apa saja gangguannya paling banyak?"*

Untuk menghentikan server: tekan `Ctrl+C` di terminal.

---

## 6. Mengganti Data Contoh dengan Data Riil

Buka `src/data.js`. Ganti isi array `FEEDERS` (daftar penyulang beserta jumlah pelanggan)
dan `INCIDENTS` (log kejadian gangguan) dengan data riil hasil magang Anda — struktur
field-nya dipertahankan sama persis supaya seluruh dashboard dan Asisten AI otomatis
mengikuti tanpa perlu mengubah kode lain.

---

## 7. Struktur Proyek

```
saidi-saifi-agent/
├── .env.example          → salin jadi .env, isi API key Gemini
├── src/
│   ├── data.js            → data mentah (FEEDERS, INCIDENTS, standar SPLN/IEEE)
│   ├── reliabilityMetrics.js → perhitungan SAIDI/SAIFI/CAIDI (satu sumber kebenaran)
│   ├── SaidiSaifiDashboard.jsx → tampilan dashboard (gauge, grafik, tabel, 5 tab)
│   ├── aiAgent.js          → integrasi Gemini: definisi tool + siklus reason-act
│   ├── AiAssistantPanel.jsx→ antarmuka obrolan tab "Asisten AI"
│   └── main.jsx            → titik masuk React
```

---

## 8. Build untuk Produksi (opsional)

Jika suatu saat perlu men-deploy dashboard ini (misalnya ke Vercel/Netlify untuk
lampiran demo online):

```bash
npm run build
```

**Peringatan keamanan:** kode ini memanggil Gemini API langsung dari browser
menggunakan API key di `.env` — cocok untuk pemakaian lokal/prototipe, **tetapi jangan
deploy hasil build ini ke domain publik tanpa memindahkan pemanggilan API ke backend**,
karena API key akan terlihat oleh siapa pun yang membuka DevTools browser. Untuk laporan
akademik dan demo lokal, cara ini sudah lazim dan aman digunakan.

---

## 9. Troubleshooting

| Gejala | Kemungkinan penyebab & solusi |
|---|---|
| `npm install` gagal | Cek versi Node dengan `node -v` — harus 20 ke atas. Update Node.js bila perlu. |
| Halaman putih / error di browser | Buka DevTools browser (`F12`) → tab Console, baca pesan error. Pastikan `npm run dev` masih berjalan di terminal. |
| Asisten AI: "API key belum diatur" | Pastikan file bernama persis `.env` (bukan `.env.example` atau `.env.txt`), lalu **restart** `npm run dev` (tekan `Ctrl+C`, jalankan lagi) — Vite hanya membaca `.env` saat start. |
| Asisten AI: error 429 | Kuota gratis per-menit tercapai. Tunggu ~30-60 detik lalu coba lagi. |
| Asisten AI: error 400/401 | API key salah/tidak valid — buat ulang di aistudio.google.com/apikey. |
| Grafik tidak muncul | Refresh browser (`Ctrl+R`); pastikan tidak ada error merah di terminal `npm run dev`. |

---

Lihat juga **`TUTORIAL_AI_CODING_ASSISTANT.md`** untuk panduan memasang asisten coding AI
gratis di VS Code (di luar proyek ini) yang bisa membantu Anda memodifikasi atau
mengembangkan proyek ini lebih lanjut.

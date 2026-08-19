# Tutorial: Asisten Coding AI Gratis di VS Code

Ini terpisah dari proyek dashboard — ini adalah alat bantu *menulis dan memahami kode*
di VS Code secara umum (termasuk untuk memodifikasi proyek `saidi-saifi-agent` ini).

## Rekomendasi: GitHub Copilot (gratis penuh untuk mahasiswa terverifikasi)

Karena Anda mahasiswa aktif, Anda kemungkinan besar memenuhi syarat **GitHub Student
Developer Pack**, yang memberi **GitHub Copilot** (paket setara Copilot Pro, normalnya
$10/bulan) **gratis** selama status mahasiswa aktif — termasuk mode agen otonom
(*Agent Mode*) yang bisa membuat/mengedit banyak file dan menjalankan perintah terminal
atas instruksi Anda.

### Langkah 1 — Pastikan email kampus jadi email utama GitHub

1. Buka [github.com/settings/emails](https://github.com/settings/emails).
2. Tambahkan email kampus Anda (mis. `nama@student.itk.ac.id`) bila belum ada, lalu verifikasi lewat inbox email tersebut.
3. Jadikan email kampus sebagai **primary email** di halaman yang sama (diperlukan supaya verifikasi status mahasiswa berhasil).

### Langkah 2 — Ajukan GitHub Student Developer Pack

1. Buka **[education.github.com/pack](https://education.github.com/pack)**.
2. Klik **"Get student benefits"**, ikuti proses verifikasi (biasanya diminta unggah bukti status mahasiswa — KTM/portal akademik, atau memakai email kampus otomatis terverifikasi).
3. Proses review biasanya beberapa hari; sekolah/kampus yang sudah ada di database GitHub bisa langsung disetujui otomatis.

### Langkah 3 — Aktifkan GitHub Copilot

1. Setelah status disetujui, buka **[github.com/settings/copilot](https://github.com/settings/copilot)**.
2. Klik **"Get access to GitHub Copilot"** / **"Get Access"** — karena status mahasiswa sudah terverifikasi, ini akan gratis tanpa diminta kartu kredit.

### Langkah 4 — Pasang di VS Code

1. Buka VS Code → tab **Extensions** (`Ctrl+Shift+X`).
2. Cari **"GitHub Copilot"** (oleh GitHub) → **Install**. Extension **"GitHub Copilot Chat"** biasanya ikut terpasang otomatis.
3. VS Code akan meminta sign in ke akun GitHub Anda — ikuti alurnya di browser, lalu kembali ke VS Code.
4. Ikon Copilot akan muncul di pojok kanan bawah / sidebar kanan sebagai tanda sudah aktif.

### Langkah 5 — Cara Pakai

- **Saran kode otomatis**: mulai mengetik di file apa pun (mis. `src/aiAgent.js`), Copilot akan menyarankan kelanjutan kode berwarna abu-abu — tekan `Tab` untuk menerima.
- **Copilot Chat**: buka panel chat (ikon di sidebar kanan, atau `Ctrl+Alt+I`), tanyakan apa saja soal kode yang sedang dibuka, misalnya *"Jelaskan cara kerja fungsi computeAll di reliabilityMetrics.js"*.
- **Agent Mode** (paling kuat): buka Copilot Chat → pilih mode **"Agent"** dari dropdown mode di atas kotak chat (atau `Ctrl+Shift+I` / `Cmd+Shift+I` di Mac) → beri instruksi tugas multi-langkah, misalnya:
  > "Tambahkan satu tool baru bernama `get_ranking_penyulang_terburuk` di aiAgent.js yang mengembalikan 3 penyulang dengan SAIDI tertinggi, lalu daftarkan di system prompt."

  Copilot akan membaca, mengedit file, dan bisa menjalankan perintah terminal secara otonom — Anda tinggal meninjau perubahan sebelum menyimpannya.
- Paket mahasiswa memakai model otomatis (Auto mode) — Anda tidak perlu memilih model secara manual, Copilot memilih yang paling sesuai untuk tiap permintaan.

---

## Alternatif Gratis Lain (kalau ingin membandingkan)

| Pilihan | Kelebihan | Catatan |
|---|---|---|
| **Gemini Code Assist** (extension VS Code dari Google) | Terintegrasi langsung dengan ekosistem Gemini yang sudah Anda pakai; punya tingkat gratis untuk individu | Kemampuan agentic-nya umumnya tidak sekuat Copilot Agent Mode saat ini |
| **Continue.dev** atau **Cline** (extension open-source) | Gratis sepenuhnya, bisa dipasangi API key Gemini Anda sendiri (jadi 1 kuota gratis untuk 2 keperluan) | Perlu sedikit konfigurasi manual (isi API key di pengaturan extension) |

Untuk mayoritas kebutuhan mengerjakan tugas kuliah dan proyek seperti ini, **GitHub
Copilot lewat Student Developer Pack** adalah titik awal paling praktis karena setup-nya
paling singkat dan Agent Mode-nya paling matang saat ini.

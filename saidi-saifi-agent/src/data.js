/* ============================================================
   DATA CONTOH (DUMMY) — Ganti dengan data riil hasil magang
   Modul ini adalah SATU-SATUNYA sumber data untuk dashboard
   MAUPUN untuk tool yang dipanggil Asisten AI, agar keduanya
   selalu konsisten satu sama lain.
   ============================================================ */

export const FEEDERS = [
  { id: "KLD", name: "Klandasan", customers: 8200 },
  { id: "GBH", name: "Gunung Bahagia", customers: 7500 },
  { id: "KJG", name: "Karang Joang", customers: 4300 },
  { id: "MGR", name: "Manggar", customers: 5100 },
  { id: "DMI", name: "Damai", customers: 6800 },
  { id: "BTK", name: "Batakan", customers: 3900 },
];
export const FMAP = Object.fromEntries(FEEDERS.map((f) => [f.id, f]));
export const TOTAL_CUSTOMERS = FEEDERS.reduce((s, f) => s + f.customers, 0);

export const MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];

export const INCIDENTS = [
  { id: 1, month: 0, date: "09 Jan 2023", feeder: "KJG", time: "09:14", duration: 142, cause: "Pohon/Vegetasi", method: "Manual" },
  { id: 2, month: 0, date: "22 Jan 2023", feeder: "KLD", time: "13:02", duration: 18, cause: "Gangguan Transien", method: "RC" },
  { id: 3, month: 1, date: "03 Feb 2023", feeder: "MGR", time: "16:45", duration: 95, cause: "Petir", method: "Manual" },
  { id: 4, month: 1, date: "19 Feb 2023", feeder: "GBH", time: "19:20", duration: 165, cause: "Peralatan", method: "Manual" },
  { id: 5, month: 2, date: "02 Mar 2023", feeder: "KJG", time: "11:05", duration: 22, cause: "Binatang", method: "RC" },
  { id: 6, month: 2, date: "15 Mar 2023", feeder: "DMI", time: "14:50", duration: 110, cause: "Pohon/Vegetasi", method: "Manual" },
  { id: 7, month: 2, date: "27 Mar 2023", feeder: "KLD", time: "07:40", duration: 15, cause: "Gangguan Transien", method: "RC" },
  { id: 8, month: 3, date: "09 Apr 2023", feeder: "MGR", time: "20:10", duration: 130, cause: "Cuaca Ekstrem", method: "Manual" },
  { id: 9, month: 3, date: "30 Apr 2023", feeder: "BTK", time: "15:55", duration: 20, cause: "Gangguan Transien", method: "RC" },
  { id: 10, month: 4, date: "14 Mei 2023", feeder: "GBH", time: "09:00", duration: 19, cause: "Gangguan Transien", method: "RC" },
  { id: 11, month: 4, date: "22 Mei 2023", feeder: "DMI", time: "12:35", duration: 88, cause: "Peralatan", method: "Manual" },
  { id: 12, month: 5, date: "16 Jun 2023", feeder: "KJG", time: "06:50", duration: 25, cause: "Binatang", method: "RC" },
  { id: 13, month: 5, date: "28 Jun 2023", feeder: "MGR", time: "21:40", duration: 16, cause: "Gangguan Transien", method: "RC" },
  { id: 14, month: 6, date: "11 Jul 2023", feeder: "BTK", time: "13:20", duration: 120, cause: "Pohon/Vegetasi", method: "Manual" },
  { id: 15, month: 6, date: "25 Jul 2023", feeder: "GBH", time: "10:10", duration: 14, cause: "Gangguan Transien", method: "RC" },
  { id: 16, month: 7, date: "08 Agu 2023", feeder: "DMI", time: "18:05", duration: 70, cause: "Peralatan", method: "Manual" },
  { id: 17, month: 7, date: "21 Agu 2023", feeder: "KLD", time: "09:45", duration: 19, cause: "Gangguan Transien", method: "RC" },
  { id: 18, month: 8, date: "14 Sep 2023", feeder: "KJG", time: "11:30", duration: 175, cause: "Pohon/Vegetasi", method: "Manual" },
  { id: 19, month: 8, date: "29 Sep 2023", feeder: "MGR", time: "15:00", duration: 21, cause: "Binatang", method: "RC" },
  { id: 20, month: 9, date: "17 Okt 2023", feeder: "BTK", time: "08:55", duration: 100, cause: "Peralatan", method: "Manual" },
  { id: 21, month: 10, date: "09 Nov 2023", feeder: "DMI", time: "19:30", duration: 155, cause: "Petir", method: "Manual" },
  { id: 22, month: 11, date: "24 Des 2023", feeder: "KLD", time: "17:15", duration: 145, cause: "Cuaca Ekstrem", method: "Manual" },
];

/* Nilai standar yang paling umum disitir pada literatur sejenis.
   Lihat catatan metodologi di bagian bawah dashboard. */
export const STANDARDS = {
  SPLN: { saidi: 21, saifi: 3.2, label: "SPLN 59:1985 / 68-2:1986" },
  IEEE: { saidi: 2.3, saifi: 1.45, caidi: 1.47, label: "IEEE Std 1366" },
};

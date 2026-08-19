import { GoogleGenAI, FunctionCallingConfigMode } from "@google/genai";
import { STANDARDS, TOTAL_CUSTOMERS } from "./data.js";
import { computeAll } from "./reliabilityMetrics.js";

/* ============================================================
   KONFIGURASI KLIEN GEMINI
   API key dibaca dari .env (VITE_GEMINI_API_KEY), GRATIS di
   https://aistudio.google.com/apikey — lihat README.md.
   ============================================================ */
const API_KEY = import.meta.env.VITE_GEMINI_API_KEY;
const MODEL = "gemini-2.5-flash"; // model tier gratis paling longgar kuotanya

let _client = null;
function getClient() {
  if (!API_KEY || API_KEY.includes("tempel_api_key")) {
    throw new Error(
      "VITE_GEMINI_API_KEY belum diisi. Salin .env.example menjadi .env lalu isi dengan API key gratis dari https://aistudio.google.com/apikey, kemudian restart `npm run dev`."
    );
  }
  if (!_client) _client = new GoogleGenAI({ apiKey: API_KEY });
  return _client;
}

/* ============================================================
   SYSTEM PROMPT
   ============================================================ */
const SYSTEM_PROMPT = `Anda adalah asisten AI yang terpasang pada dashboard evaluasi keandalan jaringan distribusi 20 kV (indeks SAIDI/SAIFI/CAIDI) DCC Kaltimra — prototipe proyek konversi mata kuliah Sistem Distribusi Tenaga Listrik (TE2515020), Institut Teknologi Kalimantan.

Aturan wajib:
1. Untuk pertanyaan tentang angka SAIDI/SAIFI/CAIDI (baik sistem maupun per penyulang), tren bulanan, penyebab gangguan, atau perbandingan metode pemulihan, WAJIB panggil tool yang sesuai. JANGAN PERNAH mengarang atau menghitung sendiri angka tersebut dari ingatan.
2. Setiap kali menyebut angka spesifik pertama kali dalam jawaban, ingatkan singkat bahwa seluruh data adalah DATA CONTOH (dummy) tahun 2023, bukan data operasional real PT PLN UP2D Kaltimra.
3. Saat relevan, bandingkan hasil terhadap standar SPLN dan IEEE Std 1366 yang dikembalikan oleh tool.
4. Anda hanya menjelaskan dan menganalisis data historis (bersifat decision-support) — Anda TIDAK mengendalikan atau memerintahkan tindakan apa pun pada sistem distribusi nyata.
5. Jawab dalam Bahasa Indonesia, ringkas (maksimal sekitar 4-5 kalimat kecuali diminta rinci), dan sertakan satuan yang tepat (jam/tahun, kali/tahun, menit, dst).`;

/* ============================================================
   DEKLARASI TOOL — skema harus JSON Schema polos (parametersJsonSchema)
   ============================================================ */
const TOOLS = [
  {
    functionDeclarations: [
      {
        name: "get_ringkasan_keandalan_sistem",
        description:
          "Mengambil ringkasan indeks keandalan sistem (SAIDI, SAIFI, CAIDI) tahun 2023 beserta perbandingan terhadap standar SPLN dan IEEE Std 1366, dan status memenuhi/belum memenuhi.",
        parametersJsonSchema: { type: "object", properties: {} },
      },
      {
        name: "get_detail_penyulang",
        description:
          "Mengambil detail indeks keandalan (SAIDI, SAIFI, CAIDI, status SPLN/IEEE) untuk satu penyulang tertentu, atau seluruh penyulang sekaligus bila feeder_id='SEMUA'.",
        parametersJsonSchema: {
          type: "object",
          properties: {
            feeder_id: {
              type: "string",
              enum: ["KLD", "GBH", "KJG", "MGR", "DMI", "BTK", "SEMUA"],
              description:
                "Kode penyulang: KLD=Klandasan, GBH=Gunung Bahagia, KJG=Karang Joang, MGR=Manggar, DMI=Damai, BTK=Batakan. Gunakan SEMUA untuk membandingkan seluruh penyulang.",
            },
          },
          required: ["feeder_id"],
        },
      },
      {
        name: "get_tren_bulanan",
        description: "Mengambil kontribusi SAIDI dan SAIFI per bulan sepanjang tahun 2023, untuk melihat pola musiman gangguan.",
        parametersJsonSchema: { type: "object", properties: {} },
      },
      {
        name: "get_analisis_penyebab_dan_pemulihan",
        description:
          "Mengambil rincian penyebab gangguan (jumlah kejadian & total durasi padam per penyebab) serta perbandingan kecepatan pemulihan Remote Control (SCADA) vs manual ke lapangan.",
        parametersJsonSchema: { type: "object", properties: {} },
      },
    ],
  },
];

/* ============================================================
   IMPLEMENTASI TOOL — memanggil ULANG computeAll() yang sama
   persis dengan yang dipakai dashboard, agar jawaban agent
   selalu konsisten dengan angka yang tampil di tab lain.
   ============================================================ */
function toolRingkasan() {
  const idx = computeAll();
  return {
    saidi_jam_per_tahun: +idx.saidiH.toFixed(2),
    saifi_kali_per_tahun: +idx.saifi.toFixed(2),
    caidi_jam_per_kejadian: +idx.caidiH.toFixed(2),
    standar_SPLN: { saidi_maks_jam: STANDARDS.SPLN.saidi, saifi_maks_kali: STANDARDS.SPLN.saifi, label: STANDARDS.SPLN.label },
    standar_IEEE: {
      saidi_maks_jam: STANDARDS.IEEE.saidi,
      saifi_maks_kali: STANDARDS.IEEE.saifi,
      caidi_maks_jam: STANDARDS.IEEE.caidi,
      label: STANDARDS.IEEE.label,
    },
    memenuhi_SPLN: idx.saidiH <= STANDARDS.SPLN.saidi && idx.saifi <= STANDARDS.SPLN.saifi,
    memenuhi_IEEE: idx.saidiH <= STANDARDS.IEEE.saidi && idx.saifi <= STANDARDS.IEEE.saifi,
    total_kejadian: idx.rcCount + idx.manCount,
    total_pelanggan: TOTAL_CUSTOMERS,
    catatan: "Seluruh angka berasal dari DATA CONTOH (dummy) tahun 2023, bukan data operasional real PT PLN.",
  };
}

function toolDetailPenyulang(args) {
  const idx = computeAll();
  const feederId = args?.feeder_id;
  if (!feederId || feederId === "SEMUA") {
    return {
      penyulang: idx.perFeeder.map((f) => ({
        id: f.id,
        nama: f.name,
        pelanggan: f.customers,
        saifi_kali: f.saifi,
        saidi_jam: +f.saidiH.toFixed(2),
        caidi_jam: +f.caidiH.toFixed(2),
        memenuhi_SPLN: f.saidiH <= STANDARDS.SPLN.saidi && f.saifi <= STANDARDS.SPLN.saifi,
      })),
    };
  }
  const f = idx.perFeeder.find((x) => x.id === feederId);
  if (!f) return { error: `feeder_id '${feederId}' tidak dikenali` };
  return {
    id: f.id,
    nama: f.name,
    pelanggan: f.customers,
    saifi_kali: f.saifi,
    saidi_jam: +f.saidiH.toFixed(2),
    caidi_jam: +f.caidiH.toFixed(2),
    jumlah_kejadian: f.count,
    memenuhi_SPLN: f.saidiH <= STANDARDS.SPLN.saidi && f.saifi <= STANDARDS.SPLN.saifi,
    memenuhi_IEEE: f.saidiH <= STANDARDS.IEEE.saidi && f.saifi <= STANDARDS.IEEE.saifi,
  };
}

function toolTrenBulanan() {
  const idx = computeAll();
  return { tren_bulanan: idx.monthly };
}

function toolPenyebabDanPemulihan() {
  const idx = computeAll();
  const penyebab = Object.entries(idx.causeMap)
    .map(([nama, d]) => ({ penyebab: nama, jumlah_kejadian: d.count, total_durasi_menit: d.duration }))
    .sort((a, b) => b.total_durasi_menit - a.total_durasi_menit);
  return {
    penyebab_gangguan: penyebab,
    pemulihan_remote_scada_rata2_menit: +idx.rcAvg.toFixed(1),
    pemulihan_manual_rata2_menit: +idx.manAvg.toFixed(1),
    rasio_manual_dibanding_remote: +(idx.manAvg / idx.rcAvg).toFixed(1),
    jumlah_kejadian_remote: idx.rcCount,
    jumlah_kejadian_manual: idx.manCount,
  };
}

function executeTool(name, args) {
  switch (name) {
    case "get_ringkasan_keandalan_sistem":
      return toolRingkasan();
    case "get_detail_penyulang":
      return toolDetailPenyulang(args || {});
    case "get_tren_bulanan":
      return toolTrenBulanan();
    case "get_analisis_penyebab_dan_pemulihan":
      return toolPenyebabDanPemulihan();
    default:
      return { error: `tool tidak dikenal: ${name}` };
  }
}

/* ============================================================
   SATU GILIRAN PERCAKAPAN — mengelola siklus reason -> act
   (panggil model, jika ada function call jalankan tool lokal,
   kirim hasilnya balik, ulangi hingga model menjawab teks).
   `history` adalah array Content[] dari giliran-giliran sebelumnya.
   ============================================================ */
export async function runConversationTurn(history, userText) {
  const client = getClient();
  let contents = [...history, { role: "user", parts: [{ text: userText }] }];
  const toolTrace = [];

  for (let iter = 0; iter < 4; iter++) {
    const response = await client.models.generateContent({
      model: MODEL,
      contents,
      config: {
        systemInstruction: SYSTEM_PROMPT,
        tools: TOOLS,
        toolConfig: { functionCallingConfig: { mode: FunctionCallingConfigMode.AUTO } },
      },
    });

    const calls = response.functionCalls;
    if (calls && calls.length > 0) {
      const modelContent = response.candidates?.[0]?.content ?? {
        role: "model",
        parts: calls.map((c) => ({ functionCall: { name: c.name, args: c.args } })),
      };
      contents = [...contents, modelContent];

      const responseParts = calls.map((c) => {
        const result = executeTool(c.name, c.args);
        toolTrace.push({ name: c.name, args: c.args || {}, result });
        return { functionResponse: { name: c.name, response: result } };
      });
      contents = [...contents, { role: "user", parts: responseParts }];
      continue;
    }

    const text = response.text || "(tidak ada jawaban teks)";
    return { text, history: [...contents, { role: "model", parts: [{ text }] }], toolTrace };
  }

  return {
    text: "Maaf, permintaan ini butuh terlalu banyak langkah tool untuk diselesaikan. Coba pertanyaan yang lebih spesifik (mis. sebutkan nama penyulang).",
    history: contents,
    toolTrace,
  };
}

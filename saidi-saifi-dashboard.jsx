import { useState } from "react";
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, BarChart, Cell,
} from "recharts";
import {
  Gauge as GaugeIcon, TrendingUp, Activity, Database, Radio, Wrench,
  Info, Zap, Clock, Users,
} from "lucide-react";

/* ============================================================
   DATA CONTOH (DUMMY) — Ganti dengan data riil hasil magang
   ============================================================ */
const FEEDERS = [
  { id: "KLD", name: "Klandasan", customers: 8200 },
  { id: "GBH", name: "Gunung Bahagia", customers: 7500 },
  { id: "KJG", name: "Karang Joang", customers: 4300 },
  { id: "MGR", name: "Manggar", customers: 5100 },
  { id: "DMI", name: "Damai", customers: 6800 },
  { id: "BTK", name: "Batakan", customers: 3900 },
];
const FMAP = Object.fromEntries(FEEDERS.map((f) => [f.id, f]));
const TOTAL_CUSTOMERS = FEEDERS.reduce((s, f) => s + f.customers, 0);

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];

const INCIDENTS = [
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
const STANDARDS = {
  SPLN: { saidi: 21, saifi: 3.2, label: "SPLN 59:1985 / 68-2:1986" },
  IEEE: { saidi: 2.3, saifi: 1.45, caidi: 1.47, label: "IEEE Std 1366" },
};

/* ============================================================
   HELPERS
   ============================================================ */
function fmt(n, d = 2) {
  return n.toFixed(d).replace(".", ",");
}
function fmtInt(n) {
  return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

function computeAll() {
  let sumRN = 0, sumN = 0;
  INCIDENTS.forEach((ev) => {
    const cust = FMAP[ev.feeder].customers;
    sumRN += ev.duration * cust;
    sumN += cust;
  });
  const saidiMin = sumRN / TOTAL_CUSTOMERS;
  const saidiH = saidiMin / 60;
  const saifi = sumN / TOTAL_CUSTOMERS;
  const caidiMin = saidiMin / saifi;
  const caidiH = caidiMin / 60;

  const perFeeder = FEEDERS.map((f) => {
    const evs = INCIDENTS.filter((e) => e.feeder === f.id);
    const sumR = evs.reduce((s, e) => s + e.duration, 0);
    const count = evs.length;
    return {
      ...f,
      count,
      sumR,
      saidiH: sumR / 60,
      saifi: count,
      caidiH: count ? sumR / count / 60 : 0,
    };
  });

  const monthly = MONTHS.map((m, i) => {
    const evs = INCIDENTS.filter((e) => e.month === i);
    const mRN = evs.reduce((s, e) => s + e.duration * FMAP[e.feeder].customers, 0);
    const mN = evs.reduce((s, e) => s + FMAP[e.feeder].customers, 0);
    return {
      bulan: m,
      saidi: +(mRN / TOTAL_CUSTOMERS).toFixed(2),
      saifi: +(mN / TOTAL_CUSTOMERS).toFixed(3),
      kejadian: evs.length,
    };
  });

  const rcEvs = INCIDENTS.filter((e) => e.method === "RC");
  const manEvs = INCIDENTS.filter((e) => e.method === "Manual");
  const rcAvg = rcEvs.reduce((s, e) => s + e.duration, 0) / rcEvs.length;
  const manAvg = manEvs.reduce((s, e) => s + e.duration, 0) / manEvs.length;

  const causeMap = {};
  INCIDENTS.forEach((e) => {
    if (!causeMap[e.cause]) causeMap[e.cause] = { count: 0, duration: 0 };
    causeMap[e.cause].count += 1;
    causeMap[e.cause].duration += e.duration;
  });

  return {
    saidiMin, saidiH, saifi, caidiMin, caidiH,
    perFeeder, monthly, rcAvg, manAvg,
    rcCount: rcEvs.length, manCount: manEvs.length, causeMap,
  };
}

/* ---- Gauge geometry helpers ---- */
function polarPoint(cx, cy, r, thetaDeg) {
  const rad = (thetaDeg * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy - r * Math.sin(rad) };
}
function arcPath(cx, cy, r, thetaStart, thetaEnd) {
  const p1 = polarPoint(cx, cy, r, thetaStart);
  const p2 = polarPoint(cx, cy, r, thetaEnd);
  const largeArc = thetaStart - thetaEnd > 180 ? 1 : 0;
  return `M ${p1.x} ${p1.y} A ${r} ${r} 0 ${largeArc} 1 ${p2.x} ${p2.y}`;
}
function thetaForValue(v, max) {
  const f = Math.max(0, Math.min(1, v / max));
  return 180 * (1 - f);
}

function verdictBadge(value, splnMax, ieeeMax) {
  const meetsIEEE = ieeeMax != null && value <= ieeeMax;
  const meetsSPLN = splnMax != null && value <= splnMax;
  if (meetsIEEE) {
    return {
      text: splnMax != null ? "Memenuhi SPLN & IEEE" : "Memenuhi standar IEEE",
      cls: "bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/30",
    };
  }
  if (meetsSPLN) {
    return {
      text: "Memenuhi SPLN, belum IEEE",
      cls: "bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/30",
    };
  }
  return {
    text: splnMax != null ? "Belum memenuhi SPLN & IEEE" : "Belum memenuhi IEEE",
    cls: "bg-rose-500/15 text-rose-400 ring-1 ring-rose-500/30",
  };
}

/* ============================================================
   SMALL COMPONENTS
   ============================================================ */
function Badge({ v }) {
  return (
    <span className={`mt-2 inline-block text-[10px] font-medium px-2.5 py-1 rounded-full whitespace-nowrap ${v.cls}`}>
      {v.text}
    </span>
  );
}

function Gauge({ label, valueLabel, unit, value, max, zones, badgeV }) {
  const cx = 100, cy = 95, r = 70, sw = 14;
  const needleTheta = thetaForValue(value, max);
  let prevVal = 0;
  const arcs = zones.map((z) => {
    const t1 = thetaForValue(prevVal, max);
    const t2 = thetaForValue(z.upTo, max);
    prevVal = z.upTo;
    return { t1, t2, color: z.color };
  });
  return (
    <div className="flex flex-col items-center bg-slate-900/60 border border-slate-800 rounded-xl p-4">
      <svg viewBox="0 0 200 108" className="w-full max-w-[190px] overflow-visible">
        {arcs.map((a, i) => (
          <path key={i} d={arcPath(cx, cy, r, a.t1, a.t2)} stroke={a.color} strokeWidth={sw} fill="none" />
        ))}
        <g
          style={{
            transform: `rotate(${90 - needleTheta}deg)`,
            transformOrigin: "100px 95px",
            transition: "transform 700ms cubic-bezier(0.34,1.56,0.64,1)",
          }}
        >
          <line x1="100" y1="95" x2="100" y2="35" stroke="#f1f5f9" strokeWidth="3" strokeLinecap="round" />
        </g>
        <circle cx="100" cy="95" r="6" fill="#f1f5f9" />
      </svg>
      <p className="font-mono text-3xl text-slate-50 -mt-2 tabular-nums">{valueLabel}</p>
      <p className="text-[11px] text-slate-500 -mt-0.5">{unit}</p>
      <p className="text-xs font-medium text-slate-300 mt-2 text-center">{label}</p>
      <Badge v={badgeV} />
    </div>
  );
}

function StatCard({ icon: Icon, label, value, sub, accent }) {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 flex items-start gap-3">
      <div className={`shrink-0 rounded-lg p-2 ${accent}`}>
        <Icon className="w-4 h-4" />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] text-slate-500 uppercase tracking-wide">{label}</p>
        <p className="text-base font-mono text-slate-50 tabular-nums leading-tight mt-0.5">{value}</p>
        {sub && <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">{sub}</p>}
      </div>
    </div>
  );
}

function MethodPill({ method }) {
  const isRC = method === "RC";
  return (
    <span
      className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full whitespace-nowrap ${
        isRC
          ? "bg-cyan-500/15 text-cyan-300 ring-1 ring-cyan-500/30"
          : "bg-slate-700/40 text-slate-300 ring-1 ring-slate-600/40"
      }`}
    >
      {isRC ? <Radio className="w-2.5 h-2.5" /> : <Wrench className="w-2.5 h-2.5" />}
      {isRC ? "Remote (SCADA)" : "Manual"}
    </span>
  );
}

const CHART_TOOLTIP_STYLE = { background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8, fontSize: 12 };

/* ============================================================
   TABS
   ============================================================ */
const TABS = [
  { id: "ringkasan", label: "Ringkasan", icon: GaugeIcon },
  { id: "tren", label: "Tren Bulanan", icon: TrendingUp },
  { id: "feeder", label: "Per Penyulang", icon: Activity },
  { id: "data", label: "Data Mentah", icon: Database },
];

/* ============================================================
   MAIN COMPONENT
   ============================================================ */
export default function SaidiSaifiDashboard() {
  const [tab, setTab] = useState("ringkasan");
  const idx = computeAll();

  const feederSorted = [...idx.perFeeder]
    .sort((a, b) => b.saidiH - a.saidiH)
    .map((f) => ({ ...f, splnOk: f.saidiH <= STANDARDS.SPLN.saidi && f.saifi <= STANDARDS.SPLN.saifi }));

  const causeList = Object.entries(idx.causeMap).sort((a, b) => b[1].duration - a[1].duration);
  const maxCauseDuration = causeList.length ? causeList[0][1].duration : 1;

  const saidiBadge = verdictBadge(idx.saidiH, STANDARDS.SPLN.saidi, STANDARDS.IEEE.saidi);
  const saifiBadge = verdictBadge(idx.saifi, STANDARDS.SPLN.saifi, STANDARDS.IEEE.saifi);
  const caidiBadge = verdictBadge(idx.caidiH, null, STANDARDS.IEEE.caidi);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans">
      <div className="max-w-5xl mx-auto p-4 sm:p-6 md:p-8 space-y-5">
        {/* HEADER */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500" />
            </span>
            <p className="text-[11px] font-medium text-slate-500 tracking-widest uppercase">
              DCC Kaltimra · Sistem Mahakam — Data Contoh
            </p>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-50 tracking-tight">
            Evaluasi Keandalan Jaringan Distribusi 20 kV
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Indeks SAIDI / SAIFI / CAIDI berbasis data historis SCADA — Tahun 2023 · 6 Penyulang Sampel
          </p>
        </div>

        {/* DISCLAIMER */}
        <div className="bg-amber-500/10 border border-amber-500/25 rounded-xl px-4 py-3 flex gap-2.5 items-start">
          <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <p className="text-xs text-amber-200/90 leading-relaxed">
            Seluruh data pada dashboard ini adalah <span className="font-semibold">data contoh (dummy)</span> untuk
            mendemonstrasikan metode perhitungan, bukan data operasional riil PT PLN UP2D Kaltimra. Ganti array{" "}
            <code className="font-mono bg-slate-900/60 px-1 rounded">INCIDENTS</code> dan{" "}
            <code className="font-mono bg-slate-900/60 px-1 rounded">FEEDERS</code> pada kode dengan data riil hasil
            magang Anda.
          </p>
        </div>

        {/* TABS */}
        <div className="flex gap-1 overflow-x-auto border-b border-slate-800">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 px-3.5 py-2.5 text-xs sm:text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                tab === t.id ? "border-cyan-400 text-slate-50" : "border-transparent text-slate-500 hover:text-slate-300"
              }`}
            >
              <t.icon className="w-3.5 h-3.5" />
              {t.label}
            </button>
          ))}
        </div>

        {/* TAB: RINGKASAN */}
        {tab === "ringkasan" && (
          <div className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Gauge
                label="SAIDI — Durasi Padam"
                valueLabel={fmt(idx.saidiH, 2)}
                unit="jam / pelanggan / tahun"
                value={idx.saidiH}
                max={24}
                zones={[
                  { upTo: STANDARDS.IEEE.saidi, color: "#10b981" },
                  { upTo: STANDARDS.SPLN.saidi, color: "#f59e0b" },
                  { upTo: 24, color: "#f43f5e" },
                ]}
                badgeV={saidiBadge}
              />
              <Gauge
                label="SAIFI — Frekuensi Padam"
                valueLabel={fmt(idx.saifi, 2)}
                unit="kali / pelanggan / tahun"
                value={idx.saifi}
                max={5}
                zones={[
                  { upTo: STANDARDS.IEEE.saifi, color: "#10b981" },
                  { upTo: STANDARDS.SPLN.saifi, color: "#f59e0b" },
                  { upTo: 5, color: "#f43f5e" },
                ]}
                badgeV={saifiBadge}
              />
              <Gauge
                label="CAIDI — Durasi per Kejadian"
                valueLabel={fmt(idx.caidiH, 2)}
                unit="jam / kejadian"
                value={idx.caidiH}
                max={2.2}
                zones={[
                  { upTo: STANDARDS.IEEE.caidi, color: "#10b981" },
                  { upTo: 2.2, color: "#f43f5e" },
                ]}
                badgeV={caidiBadge}
              />
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <StatCard
                icon={Zap}
                label="Total Kejadian"
                value={`${idx.rcCount + idx.manCount}`}
                sub="sepanjang tahun 2023"
                accent="bg-cyan-500/15 text-cyan-300"
              />
              <StatCard
                icon={Users}
                label="Total Pelanggan"
                value={fmtInt(TOTAL_CUSTOMERS)}
                sub="pada 6 penyulang sampel"
                accent="bg-violet-500/15 text-violet-300"
              />
              <StatCard
                icon={Radio}
                label="Pemulihan Remote (SCADA)"
                value={`${fmt(idx.rcAvg, 1)} menit`}
                sub={`rata-rata · ${idx.rcCount} kejadian`}
                accent="bg-emerald-500/15 text-emerald-300"
              />
              <StatCard
                icon={Wrench}
                label="Pemulihan Manual"
                value={`${fmt(idx.manAvg, 1)} menit`}
                sub={`rata-rata · ${idx.manCount} kejadian`}
                accent="bg-rose-500/15 text-rose-300"
              />
            </div>

            <div className="bg-cyan-500/10 border border-cyan-500/25 rounded-xl px-4 py-3 flex gap-2.5 items-start">
              <Zap className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <p className="text-xs text-cyan-100/90 leading-relaxed">
                <span className="font-semibold">Insight:</span> pemulihan via Remote Control SCADA rata-rata{" "}
                {fmt(idx.manAvg / idx.rcAvg, 1)}× lebih cepat dibanding penanganan manual ke lapangan (
                {fmt(idx.rcAvg, 1)} menit vs {fmt(idx.manAvg, 1)} menit). Ini bisa jadi temuan kunci di Bab IV untuk
                menunjukkan kontribusi langsung SCADA terhadap keandalan sistem.
              </p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
              <p className="text-xs font-medium text-slate-300 mb-3">Penyebab gangguan berdasarkan total durasi padam</p>
              <div className="space-y-2.5">
                {causeList.map(([cause, d]) => (
                  <div key={cause} className="flex items-center gap-3">
                    <p className="text-[11px] text-slate-400 w-32 shrink-0">{cause}</p>
                    <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-cyan-500/70 rounded-full"
                        style={{ width: `${(d.duration / maxCauseDuration) * 100}%` }}
                      />
                    </div>
                    <p className="text-[11px] font-mono text-slate-400 w-24 shrink-0 text-right">
                      {d.duration} mnt · {d.count}×
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB: TREN BULANAN */}
        {tab === "tren" && (
          <div className="space-y-4">
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
              <p className="text-xs font-medium text-slate-300 mb-1">Kontribusi bulanan terhadap SAIDI &amp; SAIFI tahunan</p>
              <p className="text-[11px] text-slate-500 mb-3">
                Nilai standar SPLN/IEEE adalah target tahunan, sehingga tidak ditampilkan sebagai garis acuan bulanan.
              </p>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={idx.monthly} margin={{ top: 10, right: 10, left: -16, bottom: 0 }}>
                  <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="bulan" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={{ stroke: "#334155" }} tickLine={false} />
                  <YAxis
                    yAxisId="left"
                    tick={{ fill: "#64748b", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    label={{ value: "SAIDI (menit)", angle: -90, position: "insideLeft", fill: "#64748b", fontSize: 10 }}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    tick={{ fill: "#64748b", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    label={{ value: "SAIFI (kali)", angle: 90, position: "insideRight", fill: "#64748b", fontSize: 10 }}
                  />
                  <Tooltip contentStyle={CHART_TOOLTIP_STYLE} labelStyle={{ color: "#94a3b8" }} itemStyle={{ color: "#f1f5f9" }} />
                  <Legend wrapperStyle={{ fontSize: 12, color: "#94a3b8" }} />
                  <Bar yAxisId="left" dataKey="saidi" name="SAIDI (menit)" fill="#22d3ee" radius={[4, 4, 0, 0]} barSize={22} />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="saifi"
                    name="SAIFI (kali)"
                    stroke="#fbbf24"
                    strokeWidth={2}
                    dot={{ r: 3, fill: "#fbbf24" }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl px-4 py-3 flex gap-2.5 items-start">
              <TrendingUp className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
              <p className="text-xs text-slate-400 leading-relaxed">
                Kontribusi SAIDI tertinggi terjadi pada Februari, November, dan Desember — bertepatan dengan musim
                hujan, di mana petir dan cuaca ekstrem lebih dominan sebagai penyebab gangguan. Pola ini bisa
                dijadikan dasar rekomendasi pemeliharaan preventif menjelang musim hujan di Bab V.
              </p>
            </div>
          </div>
        )}

        {/* TAB: PER PENYULANG */}
        {tab === "feeder" && (
          <div className="space-y-4">
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
              <p className="text-xs font-medium text-slate-300 mb-1">Peringkat penyulang berdasarkan kontribusi SAIDI</p>
              <p className="text-[11px] text-slate-500 mb-3">
                Warna hijau = memenuhi SPLN (SAIDI &amp; SAIFI) · merah = belum memenuhi salah satu indeks SPLN
              </p>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={feederSorted} layout="vertical" margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                  <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={{ stroke: "#334155" }} tickLine={false} />
                  <YAxis type="category" dataKey="name" tick={{ fill: "#cbd5e1", fontSize: 12 }} axisLine={false} tickLine={false} width={110} />
                  <Tooltip
                    contentStyle={CHART_TOOLTIP_STYLE}
                    labelStyle={{ color: "#94a3b8" }}
                    itemStyle={{ color: "#f1f5f9" }}
                    formatter={(v) => [`${fmt(v, 2)} jam`, "SAIDI"]}
                  />
                  <Bar dataKey="saidiH" radius={[0, 4, 4, 0]} barSize={18}>
                    {feederSorted.map((f, i) => (
                      <Cell key={i} fill={f.splnOk ? "#10b981" : "#f43f5e"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-500">
                      <th className="text-left font-medium px-3.5 py-2.5 whitespace-nowrap">Penyulang</th>
                      <th className="text-right font-medium px-3 py-2.5 whitespace-nowrap">Pelanggan</th>
                      <th className="text-right font-medium px-3 py-2.5 whitespace-nowrap">SAIFI (kali)</th>
                      <th className="text-right font-medium px-3 py-2.5 whitespace-nowrap">SAIDI (jam)</th>
                      <th className="text-right font-medium px-3 py-2.5 whitespace-nowrap">CAIDI (jam)</th>
                      <th className="text-left font-medium px-3.5 py-2.5 whitespace-nowrap">Status SPLN</th>
                      <th className="text-left font-medium px-3.5 py-2.5 whitespace-nowrap">Status IEEE</th>
                    </tr>
                  </thead>
                  <tbody>
                    {feederSorted.map((f) => {
                      const sBadge = verdictBadge(f.saidiH, STANDARDS.SPLN.saidi, null);
                      const sBadgeF = verdictBadge(f.saifi, STANDARDS.SPLN.saifi, null);
                      const iBadge = verdictBadge(f.saidiH, null, STANDARDS.IEEE.saidi);
                      const iBadgeF = verdictBadge(f.saifi, null, STANDARDS.IEEE.saifi);
                      const splnOk = f.saidiH <= STANDARDS.SPLN.saidi && f.saifi <= STANDARDS.SPLN.saifi;
                      const ieeeOk = f.saidiH <= STANDARDS.IEEE.saidi && f.saifi <= STANDARDS.IEEE.saifi;
                      return (
                        <tr key={f.id} className="border-b border-slate-800/60 last:border-0 hover:bg-slate-800/30">
                          <td className="px-3.5 py-2.5 font-medium text-slate-200 whitespace-nowrap">{f.name}</td>
                          <td className="px-3 py-2.5 text-right font-mono text-slate-400 tabular-nums">{fmtInt(f.customers)}</td>
                          <td className="px-3 py-2.5 text-right font-mono text-slate-300 tabular-nums">{f.saifi}</td>
                          <td className="px-3 py-2.5 text-right font-mono text-slate-300 tabular-nums">{fmt(f.saidiH, 2)}</td>
                          <td className="px-3 py-2.5 text-right font-mono text-slate-300 tabular-nums">{fmt(f.caidiH, 2)}</td>
                          <td className="px-3.5 py-2.5">
                            <span
                              className={`text-[10px] font-medium px-2 py-0.5 rounded-full whitespace-nowrap ${
                                splnOk
                                  ? "bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/30"
                                  : "bg-rose-500/15 text-rose-400 ring-1 ring-rose-500/30"
                              }`}
                            >
                              {splnOk ? "Memenuhi" : "Belum memenuhi"}
                            </span>
                          </td>
                          <td className="px-3.5 py-2.5">
                            <span
                              className={`text-[10px] font-medium px-2 py-0.5 rounded-full whitespace-nowrap ${
                                ieeeOk
                                  ? "bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/30"
                                  : "bg-rose-500/15 text-rose-400 ring-1 ring-rose-500/30"
                              }`}
                            >
                              {ieeeOk ? "Memenuhi" : "Belum memenuhi"}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB: DATA MENTAH */}
        {tab === "data" && (
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-800 flex items-center gap-2">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              <p className="text-xs font-medium text-slate-300">Log kejadian gangguan — 22 kejadian, Jan–Des 2023</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-500">
                    <th className="text-left font-medium px-3.5 py-2.5">No</th>
                    <th className="text-left font-medium px-3 py-2.5 whitespace-nowrap">Tanggal</th>
                    <th className="text-left font-medium px-3 py-2.5 whitespace-nowrap">Penyulang</th>
                    <th className="text-left font-medium px-3 py-2.5">Pukul</th>
                    <th className="text-right font-medium px-3 py-2.5 whitespace-nowrap">Durasi (mnt)</th>
                    <th className="text-left font-medium px-3 py-2.5 whitespace-nowrap">Penyebab</th>
                    <th className="text-left font-medium px-3.5 py-2.5 whitespace-nowrap">Metode</th>
                    <th className="text-right font-medium px-3.5 py-2.5 whitespace-nowrap">Pelanggan</th>
                  </tr>
                </thead>
                <tbody>
                  {INCIDENTS.map((e) => (
                    <tr key={e.id} className="border-b border-slate-800/60 last:border-0 hover:bg-slate-800/30">
                      <td className="px-3.5 py-2 font-mono text-slate-500">{e.id}</td>
                      <td className="px-3 py-2 font-mono text-slate-300 whitespace-nowrap">{e.date}</td>
                      <td className="px-3 py-2 text-slate-200 whitespace-nowrap">{FMAP[e.feeder].name}</td>
                      <td className="px-3 py-2 font-mono text-slate-400">{e.time}</td>
                      <td className="px-3 py-2 text-right font-mono text-slate-300 tabular-nums">{e.duration}</td>
                      <td className="px-3 py-2 text-slate-400 whitespace-nowrap">{e.cause}</td>
                      <td className="px-3.5 py-2">
                        <MethodPill method={e.method} />
                      </td>
                      <td className="px-3.5 py-2 text-right font-mono text-slate-400 tabular-nums whitespace-nowrap">
                        {fmtInt(FMAP[e.feeder].customers)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* FOOTER — METHODOLOGY NOTES */}
        <div className="border-t border-slate-800 pt-4 space-y-2">
          <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wide">Catatan metodologi &amp; asumsi</p>
          <ul className="text-[11px] text-slate-500 space-y-1.5 leading-relaxed list-disc pl-4">
            <li>
              SAIDI = Σ(rᵢ×Nᵢ)/N_t, SAIFI = ΣNᵢ/N_t, CAIDI = SAIDI/SAIFI — mengikuti definisi umum indeks
              keandalan distribusi.
            </li>
            <li>Asumsi: satu kejadian gangguan memutus seluruh pelanggan pada penyulang terkait (penyederhanaan umum pada studi sejenis; jika data riil mencatat pemadaman sebagian akibat manuver LBS, sesuaikan Nᵢ per kejadian).</li>
            <li>
              Nilai standar yang digunakan merujuk pada angka yang paling umum disitir pada berbagai skripsi/jurnal
              keandalan distribusi 20 kV di Indonesia: SPLN No. 59:1985 / 68-2:1986 (SAIDI ≤ 21 jam/tahun, SAIFI ≤
              3,2 kali/tahun) dan IEEE Std 1366 (SAIDI ≤ 2,3 jam/tahun, SAIFI ≤ 1,45 kali/tahun, CAIDI ≤ 1,47
              jam/kejadian). Nilai target pada dokumen SPLN asli dapat berbeda per wilayah/klasifikasi — disarankan
              verifikasi langsung ke dokumen SPLN dan dosen pembimbing.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

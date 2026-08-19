import { FEEDERS, FMAP, TOTAL_CUSTOMERS, MONTHS, INCIDENTS } from "./data.js";

/* ============================================================
   HELPERS — dipakai oleh dashboard (UI) DAN oleh tools Asisten AI,
   supaya jawaban agent selalu konsisten dengan angka di dashboard.
   ============================================================ */
export function fmt(n, d = 2) {
  return n.toFixed(d).replace(".", ",");
}
export function fmtInt(n) {
  return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

export function computeAll() {
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

export function verdictBadge(value, splnMax, ieeeMax) {
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

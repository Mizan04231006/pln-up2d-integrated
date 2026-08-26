import { LineChart } from 'lucide-react';

function MiniMetric({ label, value, loading }) {
  if (loading) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 animate-pulse">
        <div className="h-2 w-16 rounded bg-slate-800" />
        <div className="mt-3 h-4 w-20 rounded bg-slate-700" />
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
      <p className="text-[10px] uppercase tracking-[0.2em] text-slate-400">{label}</p>
      <p className="mt-2 text-sm font-semibold text-white">{value}</p>
    </div>
  );
}

function ForecastPanel({ forecast, loading }) {
  return (
    <div className="min-w-0 rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
      <div className="mb-4 flex items-center gap-3">
        <LineChart className="h-5 w-5 text-cyan-400" />
        <h2 className="text-lg font-semibold">Forecast Beban Listrik</h2>
      </div>

      {loading ? (
        <div className="space-y-4 animate-pulse">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {Array.from({ length: 4 }).map((_, idx) => (
              <MiniMetric key={idx} label="-" value="-" loading />
            ))}
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, idx) => (
              <div key={idx} className="h-7 rounded-full border border-slate-800 bg-slate-800/70" />
            ))}
          </div>
        </div>
      ) : forecast ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <MiniMetric label="Peak" value={`${forecast.summary.peak_mw.toFixed(1)} MW`} />
            <MiniMetric label="Average" value={`${forecast.summary.average_mw.toFixed(1)} MW`} />
            <MiniMetric label="Off Peak" value={`${forecast.summary.off_peak_mw.toFixed(1)} MW`} />
            <MiniMetric label="Status" value={forecast.summary.status} />
          </div>

          <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 px-3 py-2 text-xs text-cyan-200">
            {forecast.confidence_note}
          </div>

          <div className="flex max-h-36 flex-wrap gap-2 overflow-y-auto pr-1">
            {forecast.prediksi.map((item, index) => (
              <span key={`${item.hour}-${index}`} className="rounded-full border border-slate-700 px-2 py-1 text-xs text-slate-300">
                {item.hour}: {item.beban_mw.toFixed(1)} MW
              </span>
            ))}
          </div>
        </div>
      ) : (
        <p className="text-slate-400">Data forecast belum tersedia.</p>
      )}
    </div>
  );
}

export default ForecastPanel;

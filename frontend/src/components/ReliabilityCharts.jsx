import { Activity, LineChart, TrendingUp } from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

const HORIZON_OPTIONS = [
  { label: '24 Jam', value: 24 },
  { label: '3 Hari', value: 72 },
  { label: '7 Hari', value: 168 },
];

function ChartSkeleton({ height = 'h-[280px]' }) {
  return (
    <div className={`${height} animate-pulse rounded-xl border border-slate-800 bg-slate-950/60`}>
      <div className="h-full w-full bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 bg-[length:200%_100%]" />
    </div>
  );
}

function ReliabilityCharts({
  forecastSeries,
  monthlySeries,
  feederSeries,
  loadingForecast,
  loadingDashboard,
  selectedHorizon,
  onHorizonChange,
}) {
  const forecastTickInterval = Math.max(Math.floor(forecastSeries.length / 12) - 1, 0);

  return (
    <>
      <section className="mb-8 grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <div className="min-w-0 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <LineChart className="h-5 w-5 text-cyan-400" />
              <h2 className="text-lg font-semibold">Kurva Beban</h2>
            </div>
            <div className="grid grid-cols-3 gap-2 rounded-xl border border-slate-800 bg-slate-950/70 p-1">
              {HORIZON_OPTIONS.map((opt) => {
                const active = selectedHorizon === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => onHorizonChange(opt.value)}
                    className={`rounded-lg px-2 py-1.5 text-xs font-medium transition ${
                      active
                        ? 'bg-cyan-500/20 text-cyan-200'
                        : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                    }`}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>
          </div>

          {loadingForecast ? (
            <ChartSkeleton />
          ) : forecastSeries.length > 0 ? (
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={forecastSeries}>
                  <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                  <XAxis dataKey="hour" interval={forecastTickInterval} stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} domain={['dataMin - 5', 'dataMax + 5']} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#020617',
                      border: '1px solid #1e293b',
                      borderRadius: 10,
                    }}
                    formatter={(value) => [`${Number(value).toFixed(1)} MW`, 'Beban']}
                  />
                  <Legend />
                  <Area type="monotone" dataKey="bebanMW" fill="#06b6d4" fillOpacity={0.18} stroke="none" />
                  <Line type="monotone" dataKey="bebanMW" name="Prediksi Beban" stroke="#22d3ee" strokeWidth={3} dot={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-slate-400">Data kurva beban belum tersedia.</p>
          )}
        </div>

        <div className="min-w-0 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
          <div className="mb-4 flex items-center gap-3">
            <TrendingUp className="h-5 w-5 text-emerald-400" />
            <h2 className="text-lg font-semibold">Kepadatan Gangguan Bulanan</h2>
          </div>
          {loadingDashboard ? (
            <ChartSkeleton />
          ) : monthlySeries.length > 0 ? (
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlySeries}>
                  <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                  <XAxis dataKey="bulan" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#020617',
                      border: '1px solid #1e293b',
                      borderRadius: 10,
                    }}
                  />
                  <Legend />
                  <Bar dataKey="kejadian" name="Jumlah kejadian" radius={[6, 6, 0, 0]} fill="#34d399" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-slate-400">Data gangguan bulanan belum tersedia.</p>
          )}
        </div>
      </section>

      <section className="mb-8 min-w-0 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
        <div className="mb-4 flex items-center gap-3">
          <Activity className="h-5 w-5 text-amber-400" />
          <h2 className="text-lg font-semibold">Perbandingan SAIDI/SAIFI per Penyulang</h2>
        </div>
        {loadingDashboard ? (
          <ChartSkeleton height="h-[320px]" />
        ) : feederSeries.length > 0 ? (
          <div className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={feederSeries}>
                <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                <XAxis dataKey="feeder" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="left" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="right" orientation="right" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#020617',
                    border: '1px solid #1e293b',
                    borderRadius: 10,
                  }}
                />
                <Legend />
                <Bar yAxisId="left" dataKey="saidi" name="SAIDI (jam)" radius={[6, 6, 0, 0]} fill="#38bdf8" />
                <Line yAxisId="right" type="monotone" dataKey="saifi" name="SAIFI (kali)" stroke="#f59e0b" strokeWidth={2.5} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-slate-400">Data perbandingan antar penyulang belum tersedia.</p>
        )}
      </section>
    </>
  );
}

export default ReliabilityCharts;

import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  Bot,
  Gauge,
  LineChart,
  Radio,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
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

const API_BASE = 'http://localhost:8000';

function App() {
  const [keandalan, setKeandalan] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [message, setMessage] = useState('');
  const [chatReply, setChatReply] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDashboard();
    fetchForecast();
  }, []);

  const fetchDashboard = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/dashboard/keandalan`);
      const data = await res.json();
      setKeandalan(data);
    } catch (error) {
      console.error('Gagal mengambil data dashboard:', error);
    }
  };

  const fetchForecast = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/ml/forecast`);
      const data = await res.json();
      setForecast(data);
    } catch (error) {
      console.error('Gagal mengambil data forecast:', error);
    }
  };

  const handleAsk = async () => {
    if (!message.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });
      const data = await res.json();
      setChatReply(data.answer || 'Tidak ada jawaban.');
      setMessage('');
    } catch (error) {
      setChatReply('AI Agent sedang tidak tersedia saat ini.');
    } finally {
      setLoading(false);
    }
  };

  const summary = useMemo(() => keandalan?.summary ?? null, [keandalan]);
  const forecastSeries = useMemo(() => {
    return forecast?.prediksi?.map((point) => ({
      hour: point.hour,
      bebanMW: point.beban_mw,
    })) ?? [];
  }, [forecast]);

  const monthlySeries = useMemo(() => {
    return keandalan?.monthly?.map((m) => ({
      bulan: m.bulan,
      saidi: m.saidi,
      saifi: m.saifi,
      kejadian: m.kejadian,
    })) ?? [];
  }, [keandalan]);

  const feederSeries = useMemo(() => {
    return keandalan?.perFeeder?.map((f) => ({
      feeder: f.id,
      saidi: Number(f.saidiH.toFixed(2)),
      saifi: Number(f.saifi.toFixed(2)),
    })) ?? [];
  }, [keandalan]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      <div className="mx-auto max-w-7xl px-4 py-8">
        <header className="mb-8 rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-2xl shadow-slate-950/30">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-cyan-400">PLN UP2D Balikpapan</p>
              <h1 className="mt-2 text-3xl font-bold">Integrated System</h1>
            </div>
            <div className="flex items-center gap-3 rounded-xl border border-cyan-500/30 bg-cyan-500/10 px-4 py-2 text-cyan-300">
              <ShieldCheck className="h-5 w-5" />
              <span className="text-sm font-medium">Status sistem online</span>
            </div>
          </div>
        </header>

        <section className="mb-8 grid gap-4 md:grid-cols-3">
          <StatCard icon={Gauge} label="SAIDI" value={summary ? `${summary.saidiH.toFixed(2)} jam` : '--'} accent="bg-cyan-500/10 text-cyan-300" />
          <StatCard icon={Activity} label="SAIFI" value={summary ? `${summary.saifi.toFixed(3)} kali` : '--'} accent="bg-emerald-500/10 text-emerald-300" />
          <StatCard icon={TrendingUp} label="CAIDI" value={summary ? `${summary.caidiH.toFixed(2)} jam` : '--'} accent="bg-violet-500/10 text-violet-300" />
        </section>

        <section className="mb-8 grid gap-6 xl:grid-cols-[1.6fr_1fr]">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
            <div className="mb-4 flex items-center gap-3">
              <LineChart className="h-5 w-5 text-cyan-400" />
              <h2 className="text-lg font-semibold">Forecast Beban Listrik</h2>
            </div>

            {forecast ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                  <MiniMetric label="Peak" value={`${forecast.summary.peak_mw.toFixed(1)} MW`} />
                  <MiniMetric label="Average" value={`${forecast.summary.average_mw.toFixed(1)} MW`} />
                  <MiniMetric label="Off Peak" value={`${forecast.summary.off_peak_mw.toFixed(1)} MW`} />
                  <MiniMetric label="Status" value={forecast.summary.status} />
                </div>
                <div className="flex flex-wrap gap-2">
                  {forecast.prediksi.map((item, index) => (
                    <span key={`${item.hour}-${index}`} className="rounded-full border border-slate-700 px-2 py-1 text-xs text-slate-300">
                      {item.hour}: {item.beban_mw.toFixed(1)} MW
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-slate-400">Memuat data forecast...</p>
            )}
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
            <div className="mb-4 flex items-center gap-3">
              <Bot className="h-5 w-5 text-violet-400" />
              <h2 className="text-lg font-semibold">AI Agent</h2>
            </div>

            <div className="mb-4 rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-sm text-slate-300">
              <p className="font-medium text-violet-300">Pertanyaan contoh:</p>
              <p className="mt-2">“Bagaimana kondisi prediksi beban hari ini?”</p>
            </div>

            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={4}
              className="w-full rounded-xl border border-slate-700 bg-slate-950/70 p-3 text-sm text-slate-100 outline-none ring-0 placeholder:text-slate-500"
              placeholder="Tanya soal beban, SAIDI, SAIFI, atau operasional listrik..."
            />

            <button
              type="button"
              onClick={handleAsk}
              disabled={loading}
              className="mt-4 w-full rounded-xl bg-violet-600 px-4 py-2.5 font-medium text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? 'Memproses...' : 'Kirim ke AI Agent'}
            </button>

            {chatReply && (
              <div className="mt-5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3 text-sm text-emerald-200">
                {chatReply}
              </div>
            )}
          </div>
        </section>

        <section className="mb-8 grid gap-6 xl:grid-cols-[1.4fr_1fr]">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
            <div className="mb-4 flex items-center gap-3">
              <LineChart className="h-5 w-5 text-cyan-400" />
              <h2 className="text-lg font-semibold">Kurva Beban 24 Jam</h2>
            </div>
            {forecastSeries.length > 0 ? (
              <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={forecastSeries}>
                    <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                    <XAxis dataKey="hour" stroke="#94a3b8" tick={{ fontSize: 11 }} />
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
              <p className="text-slate-400">Memuat kurva beban...</p>
            )}
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
            <div className="mb-4 flex items-center gap-3">
              <TrendingUp className="h-5 w-5 text-emerald-400" />
              <h2 className="text-lg font-semibold">Kepadatan Gangguan Bulanan</h2>
            </div>
            {monthlySeries.length > 0 ? (
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
              <p className="text-slate-400">Memuat data gangguan bulanan...</p>
            )}
          </div>
        </section>

        <section className="mb-8 rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
          <div className="mb-4 flex items-center gap-3">
            <Activity className="h-5 w-5 text-amber-400" />
            <h2 className="text-lg font-semibold">Perbandingan SAIDI/SAIFI per Penyulang</h2>
          </div>
          {feederSeries.length > 0 ? (
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
            <p className="text-slate-400">Memuat perbandingan antar penyulang...</p>
          )}
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.3fr_1fr]">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
            <div className="mb-4 flex items-center gap-3">
              <Radio className="h-5 w-5 text-amber-400" />
              <h2 className="text-lg font-semibold">Performa Penyulang</h2>
            </div>
            {keandalan ? (
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="text-slate-400">
                    <tr>
                      <th className="pb-3">Penyulang</th>
                      <th className="pb-3">Pelanggan</th>
                      <th className="pb-3">SAIDI</th>
                      <th className="pb-3">SAIFI</th>
                    </tr>
                  </thead>
                  <tbody>
                    {keandalan.perFeeder.map((feeder) => (
                      <tr key={feeder.id} className="border-t border-slate-800 text-slate-200">
                        <td className="py-3">{feeder.name}</td>
                        <td className="py-3">{feeder.customers.toLocaleString()}</td>
                        <td className="py-3">{feeder.saidiH.toFixed(2)} jam</td>
                        <td className="py-3">{feeder.saifi.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-slate-400">Memuat data keandalan...</p>
            )}
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
            <div className="mb-4 flex items-center gap-3">
              <Sparkles className="h-5 w-5 text-emerald-400" />
              <h2 className="text-lg font-semibold">Insight</h2>
            </div>
            <div className="space-y-3 text-sm text-slate-300">
              <InsightItem title="Kategori" value={forecast?.summary.status ?? '--'} />
              <InsightItem title="Model" value={forecast?.summary.model ?? 'MLPRegressor'} />
              <InsightItem title="Pelanggan total" value={summary ? `${summary.totalCustomers.toLocaleString()} pelanggan` : '--'} />
              <InsightItem title="Sumber data" value="Simulasi / prototipe" />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, accent }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
      <div className="flex items-center gap-3">
        <div className={`rounded-xl p-2 ${accent}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">{label}</p>
          <p className="mt-2 text-xl font-semibold text-white">{value}</p>
        </div>
      </div>
    </div>
  );
}

function MiniMetric({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
      <p className="text-[10px] uppercase tracking-[0.2em] text-slate-400">{label}</p>
      <p className="mt-2 text-sm font-semibold text-white">{value}</p>
    </div>
  );
}

function InsightItem({ title, value }) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2">
      <span className="text-slate-400">{title}</span>
      <span className="font-medium text-slate-100">{value}</span>
    </div>
  );
}

export default App;

import { useEffect, useMemo, useState } from 'react';
import { Activity, AlertTriangle, Download, Gauge, ShieldCheck, TrendingUp } from 'lucide-react';
import ForecastPanel from './components/ForecastPanel';
import AgentPanel from './components/AgentPanel';
import ReliabilityCharts from './components/ReliabilityCharts';
import FeederTable from './components/FeederTable';

const API_BASE = 'http://localhost:8000';

function App() {
  const [keandalan, setKeandalan] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [loadingDashboard, setLoadingDashboard] = useState(true);
  const [loadingForecast, setLoadingForecast] = useState(true);
  const [selectedHorizon, setSelectedHorizon] = useState(24);
  const [backendError, setBackendError] = useState({ dashboard: false, forecast: false });
  const [message, setMessage] = useState('');
  const [chatThread, setChatThread] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDashboard();
  }, []);

  useEffect(() => {
    fetchForecast(selectedHorizon);
  }, [selectedHorizon]);

  const fetchDashboard = async () => {
    setLoadingDashboard(true);
    try {
      const res = await fetch(`${API_BASE}/api/dashboard/keandalan`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      setKeandalan(data);
      setBackendError((prev) => ({ ...prev, dashboard: false }));
    } catch (error) {
      console.error('Gagal mengambil data dashboard:', error);
      setBackendError((prev) => ({ ...prev, dashboard: true }));
    } finally {
      setLoadingDashboard(false);
    }
  };

  const fetchForecast = async (horizon = 24) => {
    setLoadingForecast(true);
    try {
      const res = await fetch(`${API_BASE}/api/ml/forecast?horizon=${horizon}`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      setForecast(data);
      setBackendError((prev) => ({ ...prev, forecast: false }));
    } catch (error) {
      console.error('Gagal mengambil data forecast:', error);
      setBackendError((prev) => ({ ...prev, forecast: true }));
    } finally {
      setLoadingForecast(false);
    }
  };

  const handleAsk = async () => {
    const userMessage = message.trim();
    if (!userMessage) return;

    const userEntry = {
      id: `${Date.now()}-user`,
      role: 'user',
      text: userMessage,
    };

    setChatThread((prev) => [...prev, userEntry]);
    setMessage('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage }),
      });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();

      setChatThread((prev) => [
        ...prev,
        {
          id: `${Date.now()}-assistant`,
          role: 'assistant',
          text: data.answer || 'Tidak ada jawaban.',
          source: data.source || 'unknown',
          toolTraces: data.tool_traces || [],
        },
      ]);
    } catch (error) {
      setChatThread((prev) => [
        ...prev,
        {
          id: `${Date.now()}-assistant-error`,
          role: 'assistant',
          text: 'AI Agent sedang tidak tersedia saat ini.',
          source: 'fallback',
          toolTraces: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const exportSummary = () => {
    const snapshot = {
      exportedAt: new Date().toISOString(),
      summary: summary
        ? {
            saidiH: summary.saidiH,
            saifi: summary.saifi,
            caidiH: summary.caidiH,
            totalCustomers: summary.totalCustomers ?? null,
          }
        : null,
      forecast: forecast?.summary ?? null,
    };
    const blob = new Blob([JSON.stringify(snapshot, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '');
    link.download = `ringkasan-dashboard-${stamp}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
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

  const hasBackendError = backendError.dashboard || backendError.forecast;
  const forecastStatus = forecast?.summary?.status ?? null;
  const forecastPeakMw = forecast?.summary?.peak_mw ?? null;

  return (
    <div className="min-h-screen overflow-x-hidden bg-slate-950 text-slate-50">
      <div className="mx-auto max-w-7xl px-4 py-8">
        <header className="mb-8 rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-2xl shadow-slate-950/30">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-cyan-400">PLN UP2D Balikpapan</p>
              <h1 className="mt-2 text-3xl font-bold">Integrated System</h1>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={exportSummary}
                disabled={!summary || !forecast}
                className="flex items-center gap-2 rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-2 text-sm font-medium text-amber-300 transition hover:bg-amber-500/20 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Download className="h-4 w-4" />
                Ekspor Ringkasan
              </button>
              <div className="flex items-center gap-3 rounded-xl border border-cyan-500/30 bg-cyan-500/10 px-4 py-2 text-cyan-300">
                <ShieldCheck className="h-5 w-5" />
                <span className="text-sm font-medium">Status sistem online</span>
              </div>
            </div>
          </div>
        </header>

        {hasBackendError && (
          <div className="mb-6 rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            Backend tidak terhubung di localhost:8000 — pastikan sudah dijalankan.
          </div>
        )}

        {forecastStatus === 'SIAGA' || forecastStatus === 'AWAS' ? (
          <div
            className={`mb-6 flex items-start gap-3 rounded-xl border px-4 py-3 ${
              forecastStatus === 'AWAS'
                ? 'border-red-500/60 bg-red-500/15 text-red-100'
                : 'border-amber-500/60 bg-amber-500/15 text-amber-100'
            }`}
          >
            <AlertTriangle
              className={`mt-0.5 h-6 w-6 shrink-0 ${forecastStatus === 'AWAS' ? 'text-red-400' : 'text-amber-400'}`}
            />
            <div>
              <p className="text-sm font-bold uppercase tracking-wide">
                Peringatan {forecastStatus}
              </p>
              <p className="mt-1 text-sm">
                {forecastStatus === 'AWAS'
                  ? `Prediksi beban puncak ${forecastPeakMw ?? '-'} MW melewati ambang kritis >105 MW. Perlu eskalasi operasional segera.`
                  : `Prediksi beban puncak ${forecastPeakMw ?? '-'} MW melewati ambang SIAGA (≥95 MW). Awasi periode beban puncak.`}
              </p>
            </div>
          </div>
        ) : null}

        <section className="mb-8 grid gap-4 md:grid-cols-3">
          <StatCard
            icon={Gauge}
            label="SAIDI"
            value={summary ? `${summary.saidiH.toFixed(2)} jam` : '--'}
            accent="bg-cyan-500/10 text-cyan-300"
            loading={loadingDashboard}
          />
          <StatCard
            icon={Activity}
            label="SAIFI"
            value={summary ? `${summary.saifi.toFixed(3)} kali` : '--'}
            accent="bg-emerald-500/10 text-emerald-300"
            loading={loadingDashboard}
          />
          <StatCard
            icon={TrendingUp}
            label="CAIDI"
            value={summary ? `${summary.caidiH.toFixed(2)} jam` : '--'}
            accent="bg-violet-500/10 text-violet-300"
            loading={loadingDashboard}
          />
        </section>

        <section className="mb-8 grid gap-6 xl:grid-cols-[1.6fr_1fr]">
          <ForecastPanel forecast={forecast} loading={loadingForecast} />
          <AgentPanel
            message={message}
            setMessage={setMessage}
            chatThread={chatThread}
            loading={loading}
            onAsk={handleAsk}
          />
        </section>

        <ReliabilityCharts
          forecastSeries={forecastSeries}
          monthlySeries={monthlySeries}
          feederSeries={feederSeries}
          loadingForecast={loadingForecast}
          loadingDashboard={loadingDashboard}
          selectedHorizon={selectedHorizon}
          onHorizonChange={setSelectedHorizon}
        />

        <FeederTable
          keandalan={keandalan}
          summary={summary}
          forecast={forecast}
          loadingDashboard={loadingDashboard}
          loadingForecast={loadingForecast}
        />
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, accent, loading }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
      <div className="flex items-center gap-3">
        <div className={`rounded-xl p-2 ${accent}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">{label}</p>
          {loading ? (
            <div className="mt-2 h-6 w-28 animate-pulse rounded bg-slate-700" />
          ) : (
            <p className="mt-2 text-xl font-semibold text-white">{value}</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;

import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Download,
  RefreshCw,
  ShieldCheck,
  Wifi,
} from 'lucide-react';
import ForecastPanel from './components/ForecastPanel';
import AgentPanel from './components/AgentPanel';
import ReliabilityCharts from './components/ReliabilityCharts';
import FeederTable from './components/FeederTable';
import plnLogo from '../../images/Logo_PLN.png';
import gedungImage from '../../images/Gedung ITK.jpeg';

const API_BASE = import.meta.env.VITE_API_BASE ? import.meta.env.VITE_API_BASE.replace(/\/+$/, '') : '';

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
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchDashboard = async () => {
    setLoadingDashboard(true);
    try {
      const res = await fetch(`${API_BASE}/api/dashboard/keandalan`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setKeandalan(await res.json());
      setBackendError((prev) => ({ ...prev, dashboard: false }));
      setLastUpdated(new Date());
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
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setForecast(await res.json());
      setBackendError((prev) => ({ ...prev, forecast: false }));
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Gagal mengambil data forecast:', error);
      setBackendError((prev) => ({ ...prev, forecast: true }));
    } finally {
      setLoadingForecast(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  useEffect(() => {
    fetchForecast(selectedHorizon);
  }, [selectedHorizon]);

  const refreshAll = () => {
    fetchDashboard();
    fetchForecast(selectedHorizon);
  };

  const handleAsk = async () => {
    const userMessage = message.trim();
    if (!userMessage) return;
    setChatThread((prev) => [...prev, { id: `${Date.now()}-user`, role: 'user', text: userMessage }]);
    setMessage('');
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
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
      console.error('Gagal menghubungi AI Agent:', error);
      setChatThread((prev) => [
        ...prev,
        {
          id: `${Date.now()}-assistant-error`,
          role: 'assistant',
          text: 'AI Agent sedang tidak tersedia saat ini. Periksa koneksi backend dan coba lagi.',
          source: 'fallback',
          toolTraces: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const summary = useMemo(() => keandalan?.summary ?? null, [keandalan]);
  const forecastSeries = useMemo(
    () => forecast?.prediksi?.map((point) => ({ hour: point.hour, bebanMW: point.beban_mw })) ?? [],
    [forecast],
  );
  const monthlySeries = useMemo(
    () => keandalan?.monthly?.map((m) => ({ bulan: m.bulan, saidi: m.saidi, saifi: m.saifi, kejadian: m.kejadian })) ?? [],
    [keandalan],
  );
  const feederSeries = useMemo(
    () =>
      keandalan?.perFeeder?.map((f) => ({
        feeder: f.id,
        saidi: Number(f.saidiH.toFixed(2)),
        saifi: Number(f.saifi.toFixed(2)),
      })) ?? [],
    [keandalan],
  );

  const hasBackendError = backendError.dashboard || backendError.forecast;
  const forecastStatus = forecast?.summary?.status ?? null;
  const forecastPeakMw = forecast?.summary?.peak_mw ?? null;
  const statusTone = forecastStatus === 'AWAS' ? 'critical' : forecastStatus === 'SIAGA' ? 'warning' : 'normal';
  const updatedLabel = lastUpdated
    ? lastUpdated.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
    : '--:--';

  const exportSummary = () => {
    const snapshot = {
      exportedAt: new Date().toISOString(),
      summary: summary
        ? { saidiH: summary.saidiH, saifi: summary.saifi, caidiH: summary.caidiH, totalCustomers: summary.totalCustomers ?? null }
        : null,
      forecast: forecast?.summary ?? null,
    };
    const blob = new Blob([JSON.stringify(snapshot, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ringkasan-dashboard-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '')}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-[#f4f7f6] text-[#1f2937]">
      <header className="border-b border-[#dce5e1] bg-[#17324d] text-white">
        <div className="mx-auto flex max-w-[1480px] flex-col gap-5 px-5 py-5 sm:px-8 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-white p-1.5">
              <img src={plnLogo} alt="Logo PLN" className="h-full w-full object-contain" />
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[#f2c94c]">UP2D Balikpapan</p>
              <h1 className="mt-1 text-xl font-semibold tracking-tight sm:text-2xl">Integrated Operations System</h1>
              <p className="mt-1 text-xs text-slate-300">Monitoring keandalan dan analisis beban distribusi</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            <div className="flex items-center gap-2 border-r border-white/15 pr-3 text-xs text-slate-300 sm:pr-4">
              <Wifi className={`h-4 w-4 ${hasBackendError ? 'text-[#f2c94c]' : 'text-[#61d69b]'}`} />
              <span>{hasBackendError ? 'Periksa koneksi' : 'Backend terhubung'}</span>
            </div>
            <button type="button" onClick={refreshAll} className="control-button control-button-dark">
              <RefreshCw className="h-4 w-4" /> Refresh data
            </button>
            <button type="button" onClick={exportSummary} disabled={!summary || !forecast} className="control-button control-button-accent disabled:cursor-not-allowed disabled:opacity-50">
              <Download className="h-4 w-4" /> Ekspor
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1480px] px-5 py-6 sm:px-8 lg:py-8">
        <section className="mb-7 grid overflow-hidden rounded-xl border border-[#dce5e1] bg-white shadow-sm lg:grid-cols-[1.35fr_1fr]">
          <div className="relative min-h-[188px] overflow-hidden p-6 sm:p-8">
            <img src={gedungImage} alt="" className="absolute inset-0 h-full w-full object-cover object-center opacity-20" />
            <div className="absolute inset-0 bg-gradient-to-r from-white via-white/95 to-white/50" />
            <div className="relative">
              <p className="section-kicker">Pusat kendali distribusi</p>
              <h2 className="mt-2 max-w-xl text-2xl font-semibold tracking-tight text-[#17324d] sm:text-3xl">Visibilitas operasi jaringan dalam satu layar.</h2>
              <p className="mt-3 max-w-lg text-sm leading-6 text-[#667085]">Pantau indikator keandalan, kecenderungan gangguan, dan proyeksi beban untuk mendukung keputusan operasional UP2D.</p>
            </div>
          </div>
          <div className="flex items-center border-t border-[#e7eeeb] bg-[#f8faf9] p-6 lg:border-l lg:border-t-0 sm:p-8">
            <div className="w-full">
              <div className="flex items-center justify-between">
                <div>
                  <p className="section-kicker">Status sistem</p>
                  <p className="mt-2 text-lg font-semibold text-[#17324d]">{hasBackendError ? 'Data perlu diperiksa' : 'Operasional normal'}</p>
                </div>
                <div className={`status-dot status-dot-${hasBackendError ? 'warning' : 'normal'}`} />
              </div>
              <div className="mt-5 grid grid-cols-2 gap-4 border-t border-[#dce5e1] pt-4 text-xs">
                <div><p className="text-[#667085]">Pembaruan terakhir</p><p className="mt-1 font-semibold text-[#1f2937]">{updatedLabel} WITA</p></div>
                <div><p className="text-[#667085]">Horizon forecast</p><p className="mt-1 font-semibold text-[#1f2937]">{selectedHorizon} jam</p></div>
              </div>
            </div>
          </div>
        </section>

        {hasBackendError && <div className="mb-6 flex items-start gap-3 rounded-lg border border-[#e8c878] bg-[#fff9e8] px-4 py-3 text-sm text-[#765b15]"><AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" /><p>Backend tidak terhubung. Pastikan layanan FastAPI berjalan, lalu tekan Refresh data.</p></div>}

        {(forecastStatus === 'SIAGA' || forecastStatus === 'AWAS') && (
          <div className={`mb-6 flex items-start gap-3 rounded-lg border px-4 py-3 text-sm ${statusTone === 'critical' ? 'border-[#e5aaaa] bg-[#fff2f2] text-[#8c2f2f]' : 'border-[#e8c878] bg-[#fff9e8] text-[#765b15]'}`}>
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
            <div><p className="font-semibold uppercase tracking-wide">Peringatan {forecastStatus}</p><p className="mt-1">{statusTone === 'critical' ? `Prediksi beban puncak ${forecastPeakMw ?? '-'} MW melewati ambang kritis >105 MW.` : `Prediksi beban puncak ${forecastPeakMw ?? '-'} MW mendekati ambang siaga (≥95 MW).`}</p></div>
          </div>
        )}

        <section className="mb-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="SAIDI" value={summary ? `${summary.saidiH.toFixed(2)} jam` : '--'} detail="Indeks durasi gangguan" icon={ShieldCheck} tone="green" loading={loadingDashboard} />
          <StatCard label="SAIFI" value={summary ? `${summary.saifi.toFixed(3)} kali` : '--'} detail="Frekuensi gangguan rata-rata" icon={Activity} tone="navy" loading={loadingDashboard} />
          <StatCard label="CAIDI" value={summary ? `${summary.caidiH.toFixed(2)} jam` : '--'} detail="Durasi rata-rata per gangguan" icon={RefreshCw} tone="yellow" loading={loadingDashboard} />
          <StatCard label="Pelanggan terpantau" value={summary ? summary.totalCustomers.toLocaleString('id-ID') : '--'} detail="Akumulasi seluruh penyulang" icon={Wifi} tone="red" loading={loadingDashboard} />
        </section>

        <section className="mb-7 grid gap-6 xl:grid-cols-[1.55fr_1fr]">
          <ForecastPanel forecast={forecast} loading={loadingForecast} />
          <AgentPanel message={message} setMessage={setMessage} chatThread={chatThread} loading={loading} onAsk={handleAsk} />
        </section>

        <ReliabilityCharts forecastSeries={forecastSeries} monthlySeries={monthlySeries} feederSeries={feederSeries} loadingForecast={loadingForecast} loadingDashboard={loadingDashboard} selectedHorizon={selectedHorizon} onHorizonChange={setSelectedHorizon} />
        <FeederTable keandalan={keandalan} summary={summary} forecast={forecast} loadingDashboard={loadingDashboard} loadingForecast={loadingForecast} />
      </main>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, detail, tone, loading }) {
  return (
    <div className="metric-card">
      <div className={`metric-icon metric-icon-${tone}`}><Icon className="h-5 w-5" /></div>
      <div className="min-w-0"><p className="section-kicker">{label}</p>{loading ? <div className="mt-2 h-7 w-28 animate-pulse rounded bg-[#e7eeeb]" /> : <p className="mt-1 truncate text-2xl font-semibold tracking-tight text-[#17324d]">{value}</p>}<p className="mt-1 text-xs text-[#667085]">{detail}</p></div>
    </div>
  );
}

export default App;

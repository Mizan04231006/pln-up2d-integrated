import { Radio, Sparkles } from 'lucide-react';

function FeederTable({ keandalan, summary, forecast, loadingDashboard, loadingForecast }) {
  return (
    <section className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
      <div className="panel min-w-0">
        <div className="panel-heading"><div className="flex items-center gap-3"><div className="panel-icon panel-icon-navy"><Radio className="h-5 w-5" /></div><div><p className="section-kicker">Performa jaringan</p><h2 className="panel-title">Daftar penyulang</h2></div></div>{keandalan?.perFeeder && <span className="text-xs text-[#667085]">{keandalan.perFeeder.length} penyulang</span>}</div>
        {loadingDashboard ? <div className="space-y-3">{Array.from({ length: 5 }).map((_, idx) => <div key={idx} className="h-10 animate-pulse rounded bg-[#f4f7f6]" />)}</div> : keandalan ? <div className="overflow-x-auto"><table className="data-table"><thead><tr><th>Penyulang</th><th className="text-right">Pelanggan</th><th className="text-right">SAIDI</th><th className="text-right">SAIFI</th></tr></thead><tbody>{keandalan.perFeeder.map((feeder) => <tr key={feeder.id}><td><p className="font-semibold text-[#17324d]">{feeder.name}</p><p className="text-[11px] text-[#667085]">{feeder.id}</p></td><td className="text-right">{feeder.customers.toLocaleString('id-ID')}</td><td className="text-right">{feeder.saidiH.toFixed(2)} jam</td><td className="text-right">{feeder.saifi.toFixed(2)}</td></tr>)}</tbody></table></div> : <p className="py-10 text-center text-sm text-[#667085]">Data performa penyulang belum tersedia.</p>}
      </div>
      <div className="panel min-w-0">
        <div className="panel-heading"><div className="flex items-center gap-3"><div className="panel-icon panel-icon-yellow"><Sparkles className="h-5 w-5" /></div><div><p className="section-kicker">Ringkasan model</p><h2 className="panel-title">Insight operasional</h2></div></div></div>
        <div className="space-y-3 text-sm"><InsightItem title="Kategori beban" value={forecast?.summary?.status ?? '--'} loading={loadingForecast} /><InsightItem title="Model forecasting" value={forecast?.summary?.model ?? '--'} loading={loadingForecast} /><InsightItem title="Pelanggan total" value={summary ? `${summary.totalCustomers.toLocaleString('id-ID')} pelanggan` : '--'} loading={loadingDashboard} /><InsightItem title="Sumber dashboard" value="Data backend FastAPI" loading={false} /></div>
      </div>
    </section>
  );
}

function InsightItem({ title, value, loading }) {
  return <div className="flex items-center justify-between gap-4 border-b border-[#e7eeeb] py-2.5 last:border-0"><span className="text-[#667085]">{title}</span>{loading ? <span className="h-4 w-20 animate-pulse rounded bg-[#e7eeeb]" /> : <span className="text-right font-semibold text-[#17324d]">{value}</span>}</div>;
}

export default FeederTable;

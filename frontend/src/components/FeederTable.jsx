import { Radio, Sparkles } from 'lucide-react';

function InsightItem({ title, value, loading }) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2">
      <span className="text-slate-400">{title}</span>
      {loading ? <span className="h-4 w-20 animate-pulse rounded bg-slate-700" /> : <span className="font-medium text-slate-100">{value}</span>}
    </div>
  );
}

function FeederTable({ keandalan, summary, forecast, loadingDashboard, loadingForecast }) {
  return (
    <section className="grid gap-6 xl:grid-cols-[1.3fr_1fr]">
      <div className="min-w-0 rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
        <div className="mb-4 flex items-center gap-3">
          <Radio className="h-5 w-5 text-amber-400" />
          <h2 className="text-lg font-semibold">Performa Penyulang</h2>
        </div>

        {loadingDashboard ? (
          <div className="space-y-3 animate-pulse">
            {Array.from({ length: 6 }).map((_, idx) => (
              <div key={idx} className="h-8 rounded bg-slate-800" />
            ))}
          </div>
        ) : keandalan ? (
          <div className="overflow-x-auto">
            <table className="min-w-[520px] text-left text-sm">
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
          <p className="text-slate-400">Data performa penyulang belum tersedia.</p>
        )}
      </div>

      <div className="min-w-0 rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
        <div className="mb-4 flex items-center gap-3">
          <Sparkles className="h-5 w-5 text-emerald-400" />
          <h2 className="text-lg font-semibold">Insight</h2>
        </div>
        <div className="space-y-3 text-sm text-slate-300">
          <InsightItem title="Kategori" value={forecast?.summary.status ?? '--'} loading={loadingForecast} />
          <InsightItem title="Model" value={forecast?.summary.model ?? 'MLPRegressor'} loading={loadingForecast} />
          <InsightItem
            title="Pelanggan total"
            value={summary ? `${summary.totalCustomers.toLocaleString()} pelanggan` : '--'}
            loading={loadingDashboard}
          />
          <InsightItem title="Sumber data" value="Simulasi / prototipe" loading={false} />
        </div>
      </div>
    </section>
  );
}

export default FeederTable;

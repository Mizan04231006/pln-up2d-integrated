import { useMemo, useState } from 'react';
import { BrainCircuit, LineChart } from 'lucide-react';
import { CartesianGrid, Line, LineChart as RechartsLineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const HORIZON_OPTIONS = [
  { label: '24 jam', value: 24 },
  { label: '3 hari', value: 72 },
  { label: '7 hari', value: 168 },
];

const tooltipStyle = { background: '#17324d', border: 0, borderRadius: 6, color: '#fff', fontSize: 12 };

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;

  const rows = payload.map((entry) => {
    const rawName = entry.name || entry.dataKey || 'Series';
    const labelText = rawName === 'aktual' ? 'Data aktual hasil olahan' : rawName;
    return {
      label: labelText,
      value: Number(entry.value ?? 0).toFixed(3),
      color: entry.color || '#17324d',
    };
  });

  return (
    <div style={{ background: '#17324d', color: '#fff', borderRadius: 8, padding: '8px 10px', fontSize: 12, boxShadow: '0 10px 20px rgba(23,50,77,0.15)' }}>
      <div style={{ marginBottom: 6, fontWeight: 600 }}>{label}</div>
      <div style={{ display: 'grid', gap: 4 }}>
        {rows.map((row) => (
          <div key={row.label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 8, height: 8, borderRadius: 999, background: row.color, display: 'inline-block' }} />
              {row.label}
            </span>
            <strong>{row.value} MW</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

function OutageModelPanel({ evaluation, loading }) {
  const [selectedWindow, setSelectedWindow] = useState(24);
  const models = evaluation?.models ?? {};
  const setting1 = models.setting_1;
  const setting2 = models.setting_2;
  const sample = setting1?.sample ?? [];
  const setting2Sample = setting2?.sample ?? [];
  const series = useMemo(
    () =>
      sample.map((point, index) => ({
        waktu: point.waktu,
        aktual: point.aktual_mw,
        setting1: point.prediksi_mw,
        setting2: setting2Sample[index]?.prediksi_mw ?? null,
      })),
    [sample, setting2Sample],
  );
  const visibleSeries = useMemo(() => series.slice(-selectedWindow), [series, selectedWindow]);
  const comparison = Object.values(models);

  return (
    <section className="panel mb-7 min-w-0">
      <div className="panel-heading">
        <div className="flex items-center gap-3">
          <div className="panel-icon panel-icon-green"><BrainCircuit className="h-5 w-5" /></div>
          <div><p className="section-kicker">Evaluasi neural network</p><h2 className="panel-title">Forecast beban padam</h2></div>
        </div>
        {evaluation?.ready && <div className="segmented-control">{HORIZON_OPTIONS.map((option) => <button key={option.value} type="button" onClick={() => setSelectedWindow(option.value)} className={selectedWindow === option.value ? 'active' : ''}>{option.label}</button>)}</div>}
      </div>
      {loading ? <div className="h-[320px] animate-pulse rounded-lg bg-[#f4f7f6]" /> : !evaluation?.ready || !setting1 ? (
        <p className="py-16 text-center text-sm text-[#667085]">Evaluasi model beban padam belum tersedia.</p>
      ) : (
        <>
          <div className="mb-5 grid gap-3 sm:grid-cols-4">
            <Metric label="Model aktif" value="Setting 1" />
            <Metric label="MAPE" value={`${setting1.metrics.mape.toFixed(2)}%`} />
            <Metric label="RMSE" value={`${setting1.metrics.rmse_mw.toFixed(3)} MW`} />
            <Metric label="R²" value={setting1.metrics.r2.toFixed(3)} />
          </div>

          <div className="mb-3 flex flex-wrap items-center gap-4 text-[11px] text-[#667085]">
            <LegendItem color="#17324d" label="Data aktual hasil olahan" />
            <LegendItem color="#008c45" label="Setting 1" />
            <LegendItem color="#d64545" label="Setting 2" />
          </div>

          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <RechartsLineChart data={visibleSeries} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
                <CartesianGrid stroke="#e7eeeb" vertical={false} />
                <XAxis dataKey="waktu" interval={Math.max(Math.floor(visibleSeries.length / 10) - 1, 0)} tick={{ fontSize: 10, fill: '#667085' }} tickLine={false} axisLine={false} />
                <YAxis unit=" MW" tick={{ fontSize: 10, fill: '#667085' }} tickLine={false} axisLine={false} width={55} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="aktual" name="aktual" stroke="#17324d" strokeWidth={2.5} dot={{ r: 1.5 }} activeDot={{ r: 4 }} />
                <Line type="monotone" dataKey="setting1" name="Setting 1" stroke="#008c45" strokeWidth={2} dot={{ r: 1.2 }} activeDot={{ r: 4 }} />
                <Line type="monotone" dataKey="setting2" name="Setting 2" stroke="#d64545" strokeWidth={2} dot={{ r: 1.2 }} activeDot={{ r: 4 }} />
              </RechartsLineChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 grid gap-3 border-t border-[#e7eeeb] pt-4 md:grid-cols-2">
            {comparison.map((model) => (
              <div key={model.label} className="rounded-lg border border-[#e7eeeb] bg-[#f8faf9] p-3 text-xs">
                <div className="flex items-center gap-2 font-semibold text-[#17324d]"><LineChart className="h-3.5 w-3.5 text-[#008c45]" />{model.label} · {model.architecture.join('-')}</div>
                <div className="mt-2 grid grid-cols-4 gap-2 text-[#667085]">
                  <span>MAPE <b className="text-[#17324d]">{model.metrics.mape.toFixed(2)}%</b></span>
                  <span>RMSE <b className="text-[#17324d]">{model.metrics.rmse_mw.toFixed(3)}</b></span>
                  <span>MAE <b className="text-[#17324d]">{model.metrics.mae_mw.toFixed(3)}</b></span>
                  <span>R² <b className="text-[#17324d]">{model.metrics.r2.toFixed(3)}</b></span>
                </div>
              </div>
            ))}
          </div>
          <p className="mt-3 text-xs leading-5 text-[#667085]">Data aktual pada kurva adalah hasil olahan dari data mentah beban padam dan merupakan estimasi dari rekap kejadian, bukan pengukuran SCADA real-time.</p>
        </>
      )}
    </section>
  );
}

function LegendItem({ color, label }) {
  return <div className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />{label}</div>;
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-[#e7eeeb] bg-[#f8faf9] p-3"><p className="text-[10px] font-semibold uppercase tracking-wider text-[#667085]">{label}</p><p className="mt-1 text-sm font-semibold text-[#17324d]">{value}</p></div>;
}

export default OutageModelPanel;

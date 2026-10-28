import { Activity, Clock3, Cpu, LineChart, TrendingUp } from 'lucide-react';
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

function ForecastPanel({ forecast, loading }) {
  const series = forecast?.prediksi?.map((item) => ({ hour: item.hour, beban: item.beban_mw })) ?? [];

  return (
    <section className="panel min-w-0">
      <div className="panel-heading">
        <div className="flex items-center gap-3">
          <div className="panel-icon panel-icon-green"><LineChart className="h-5 w-5" /></div>
          <div><p className="section-kicker">Analisis beban</p><h2 className="panel-title">Forecast beban padam (hasil olah data mentah)</h2></div>
        </div>
        {forecast?.summary?.status && <span className={`status-label status-label-${forecast.summary.status === 'AWAS' ? 'critical' : forecast.summary.status === 'SIAGA' ? 'warning' : 'normal'}`}>{forecast.summary.status}</span>}
      </div>

      {loading ? (
        <div className="space-y-4"><div className="h-[230px] animate-pulse rounded-lg bg-[#f4f7f6]" /><div className="grid grid-cols-3 gap-3">{[1, 2, 3].map((item) => <div key={item} className="h-14 animate-pulse rounded-lg bg-[#f4f7f6]" />)}</div></div>
      ) : forecast ? (
        <>
          <div className="mb-4 grid grid-cols-3 gap-3">
            <MiniMetric icon={TrendingUp} label="Puncak" value={`${forecast.summary.peak_mw.toFixed(1)} MW`} />
            <MiniMetric icon={Activity} label="Rata-rata" value={`${forecast.summary.average_mw.toFixed(1)} MW`} />
            <MiniMetric icon={Clock3} label="Horizon" value={`${series.length} jam`} />
          </div>
          <div className="h-[230px] w-full">
            {series.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={series} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
                  <defs><linearGradient id="forecastFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#008c45" stopOpacity={0.25} /><stop offset="100%" stopColor="#008c45" stopOpacity={0} /></linearGradient></defs>
                  <CartesianGrid stroke="#e7eeeb" vertical={false} />
                  <XAxis dataKey="hour" tick={{ fontSize: 10, fill: '#667085' }} tickLine={false} axisLine={false} minTickGap={18} />
                  <YAxis unit=" MW" tick={{ fontSize: 10, fill: '#667085' }} tickLine={false} axisLine={false} width={55} />
                  <Tooltip contentStyle={{ background: '#17324d', border: 0, borderRadius: 6, color: '#fff', fontSize: 12 }} formatter={(value) => [`${Number(value).toFixed(1)} MW`, 'Beban padam prediksi']} />
                  <Area type="monotone" dataKey="beban" stroke="none" fill="url(#forecastFill)" />
                  <Line type="monotone" dataKey="beban" name="Prediksi" stroke="#008c45" strokeWidth={2.5} dot={false} />
                </ComposedChart>
              </ResponsiveContainer>
            ) : <p className="pt-16 text-center text-sm text-[#667085]">Data kurva beban belum tersedia.</p>}
          </div>
          <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-[#e7eeeb] pt-3 text-xs text-[#667085]">
            <span className="flex items-center gap-1.5"><Cpu className="h-3.5 w-3.5" /> Model: {forecast.summary.model ?? 'Tidak tersedia'}</span>
            <span>{forecast.confidence_note}</span>
          </div>
        </>
      ) : <p className="py-16 text-center text-sm text-[#667085]">Data forecast belum tersedia.</p>}
    </section>
  );
}

function MiniMetric({ icon: Icon, label, value }) {
  return <div className="rounded-lg border border-[#e7eeeb] bg-[#f8faf9] p-3"><p className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-[#667085]"><Icon className="h-3.5 w-3.5 text-[#008c45]" /> {label}</p><p className="mt-1 text-sm font-semibold text-[#17324d]">{value}</p></div>;
}

export default ForecastPanel;

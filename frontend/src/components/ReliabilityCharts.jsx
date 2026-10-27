import { Activity, BarChart3, LineChart } from 'lucide-react';
import { Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const HORIZON_OPTIONS = [{ label: '24 jam', value: 24 }, { label: '3 hari', value: 72 }, { label: '7 hari', value: 168 }];
const tooltipStyle = { background: '#17324d', border: 0, borderRadius: 6, color: '#fff', fontSize: 12 };

function ReliabilityCharts({ forecastSeries, monthlySeries, feederSeries, loadingForecast, loadingDashboard, selectedHorizon, onHorizonChange }) {
  const forecastTickInterval = Math.max(Math.floor(forecastSeries.length / 10) - 1, 0);
  const topFeederSeries = feederSeries.slice(0, 20);
  return (
    <>
      <section className="mb-7 grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <ChartPanel icon={LineChart} kicker="Prediksi model" title="Kurva beban" action={<div className="segmented-control">{HORIZON_OPTIONS.map((option) => <button key={option.value} type="button" onClick={() => onHorizonChange(option.value)} className={selectedHorizon === option.value ? 'active' : ''}>{option.label}</button>)}</div>}>
          {loadingForecast ? <ChartSkeleton /> : forecastSeries.length > 0 ? <div className="h-[280px]"><ResponsiveContainer width="100%" height="100%"><ComposedChart data={forecastSeries} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}><CartesianGrid stroke="#e7eeeb" vertical={false} /><XAxis dataKey="hour" interval={forecastTickInterval} tick={{ fontSize: 10, fill: '#667085' }} tickLine={false} axisLine={false} /><YAxis unit=" MW" tick={{ fontSize: 10, fill: '#667085' }} tickLine={false} axisLine={false} width={55} /><Tooltip contentStyle={tooltipStyle} formatter={(value) => [`${Number(value).toFixed(1)} MW`, 'Beban']} /><Line type="monotone" dataKey="bebanMW" name="Prediksi beban" stroke="#008c45" strokeWidth={2.5} dot={false} /></ComposedChart></ResponsiveContainer></div> : <EmptyState text="Data kurva beban belum tersedia." />}
        </ChartPanel>
        <ChartPanel icon={BarChart3} kicker="Riwayat gangguan" title="Kejadian bulanan">
          {loadingDashboard ? <ChartSkeleton /> : monthlySeries.length > 0 ? <div className="h-[280px]"><ResponsiveContainer width="100%" height="100%"><ComposedChart data={monthlySeries} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}><CartesianGrid stroke="#e7eeeb" vertical={false} /><XAxis dataKey="bulan" tick={{ fontSize: 10, fill: '#667085' }} tickLine={false} axisLine={false} /><YAxis tick={{ fontSize: 10, fill: '#667085' }} tickLine={false} axisLine={false} width={32} /><Tooltip contentStyle={tooltipStyle} /><Bar dataKey="kejadian" name="Jumlah kejadian" fill="#f2c94c" radius={[3, 3, 0, 0]} /></ComposedChart></ResponsiveContainer></div> : <EmptyState text="Data gangguan bulanan belum tersedia." />}
        </ChartPanel>
      </section>
      <section className="panel mb-7 min-w-0">
        <div className="panel-heading"><div className="flex items-center gap-3"><div className="panel-icon panel-icon-yellow"><Activity className="h-5 w-5" /></div><div><p className="section-kicker">Perbandingan indikator</p><h2 className="panel-title">Keandalan per penyulang</h2></div></div><span className="hidden text-xs text-[#667085] sm:block">SAIDI dalam jam · SAIFI dalam kali</span></div>
        {loadingDashboard ? <ChartSkeleton height="h-[320px]" /> : topFeederSeries.length > 0 ? <div className="h-[320px]"><ResponsiveContainer width="100%" height="100%"><ComposedChart data={topFeederSeries} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}><CartesianGrid stroke="#e7eeeb" vertical={false} /><XAxis dataKey="feeder" tick={{ fontSize: 10, fill: '#667085' }} tickLine={false} axisLine={false} /><YAxis yAxisId="left" tick={{ fontSize: 10, fill: '#667085' }} tickLine={false} axisLine={false} width={36} /><YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10, fill: '#667085' }} tickLine={false} axisLine={false} width={36} /><Tooltip contentStyle={tooltipStyle} /><Bar yAxisId="left" dataKey="saidi" name="SAIDI (jam)" fill="#17324d" radius={[3, 3, 0, 0]} /><Line yAxisId="right" type="monotone" dataKey="saifi" name="SAIFI (kali)" stroke="#d64545" strokeWidth={2.5} dot={{ r: 2 }} /></ComposedChart></ResponsiveContainer></div> : <EmptyState text="Data perbandingan antar penyulang belum tersedia." />}
      </section>
    </>
  );
}

function ChartPanel({ icon: Icon, kicker, title, action, children }) {
  return <section className="panel min-w-0 overflow-hidden"><div className="panel-heading"><div className="flex items-center gap-3"><div className="panel-icon panel-icon-green"><Icon className="h-5 w-5" /></div><div><p className="section-kicker">{kicker}</p><h2 className="panel-title">{title}</h2></div></div>{action}</div>{children}</section>;
}

function ChartSkeleton({ height = 'h-[280px]' }) { return <div className={`${height} animate-pulse rounded-lg bg-[#f4f7f6]`} />; }
function EmptyState({ text }) { return <div className="flex h-[280px] items-center justify-center text-sm text-[#667085]">{text}</div>; }

export default ReliabilityCharts;

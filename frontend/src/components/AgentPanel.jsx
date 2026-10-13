import { Fragment } from 'react';
import { Bot, Send, Wrench } from 'lucide-react';

function AgentPanel({ message, setMessage, chatThread, loading, onAsk }) {
  return (
    <section className="panel flex min-h-[390px] min-w-0 flex-col">
      <div className="panel-heading">
        <div className="flex items-center gap-3">
          <div className="panel-icon panel-icon-navy"><Bot className="h-5 w-5" /></div>
          <div><p className="section-kicker">Asisten operasional</p><h2 className="panel-title">AI Agent UP2D</h2></div>
        </div>
        <span className="text-xs text-[#667085]">Analisis berbasis data</span>
      </div>
      <div className="mb-4 rounded-lg border-l-2 border-[#f2c94c] bg-[#fff9e8] px-3 py-2.5 text-xs leading-5 text-[#765b15]">Tanyakan kondisi SAIDI/SAIFI, proyeksi beban, atau ringkasan operasional jaringan.</div>
      <div className="mb-3 min-h-0 flex-1 space-y-3 overflow-y-auto pr-1">
        {chatThread.length === 0 ? <div className="flex h-full min-h-[130px] items-center justify-center rounded-lg border border-dashed border-[#cbd8d2] px-4 text-center text-xs leading-5 text-[#667085]">Belum ada percakapan.<br />Mulai dengan pertanyaan analisis.</div> : chatThread.map((entry) => (
          <Fragment key={entry.id}>
            {entry.role === 'assistant' && entry.toolTraces?.length > 0 && entry.toolTraces.map((trace, idx) => <div key={`${entry.id}-${idx}`} className="flex gap-2 rounded-md bg-[#f8faf9] px-3 py-2 font-mono text-[10px] text-[#667085]"><Wrench className="mt-0.5 h-3 w-3 shrink-0 text-[#f2a900]" /><span><b className="text-[#17324d]">{trace.tool}</b> {String(trace.summary ?? '')}</span></div>)}
            <div className={`rounded-lg px-3 py-2.5 text-sm leading-5 ${entry.role === 'user' ? 'ml-8 bg-[#eaf4ef] text-[#17324d]' : 'mr-3 border border-[#e7eeeb] bg-white text-[#334155]'}`}><p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-[#667085]">{entry.role === 'user' ? 'Anda' : `AI Agent${entry.source ? ` · ${entry.source}` : ''}`}</p><p className="whitespace-pre-wrap">{entry.text}</p></div>
          </Fragment>
        ))}
        {loading && <div className="mr-3 animate-pulse rounded-lg border border-[#e7eeeb] bg-[#f8faf9] px-3 py-2.5 text-sm text-[#667085]">AI Agent sedang menyusun analisis...</div>}
      </div>
      <form onSubmit={(event) => { event.preventDefault(); onAsk(); }} className="flex items-end gap-2 border-t border-[#e7eeeb] pt-3">
        <textarea value={message} onChange={(event) => setMessage(event.target.value)} rows={2} className="field min-h-[48px] resize-none" placeholder="Tulis pertanyaan..." aria-label="Pertanyaan untuk AI Agent" />
        <button type="submit" disabled={loading || !message.trim()} className="send-button" aria-label="Kirim pertanyaan"><Send className="h-4 w-4" /></button>
      </form>
    </section>
  );
}

export default AgentPanel;

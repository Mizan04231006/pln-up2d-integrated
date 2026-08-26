import { Fragment } from 'react';
import { Bot, Wrench } from 'lucide-react';

function AgentPanel({ message, setMessage, chatThread, loading, onAsk }) {
  return (
    <div className="min-w-0 rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
      <div className="mb-4 flex items-center gap-3">
        <Bot className="h-5 w-5 text-violet-400" />
        <h2 className="text-lg font-semibold">AI Agent</h2>
      </div>

      <div className="mb-4 rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-sm text-slate-300">
        <p className="font-medium text-violet-300">Pertanyaan contoh:</p>
        <p className="mt-2">“Bagaimana kondisi prediksi beban 3 hari ke depan?”</p>
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
        onClick={onAsk}
        disabled={loading}
        className="mt-4 w-full rounded-xl bg-violet-600 px-4 py-2.5 font-medium text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? 'Memproses...' : 'Kirim ke AI Agent'}
      </button>

      <div className="mt-5 max-h-80 space-y-3 overflow-y-auto pr-1">
        {chatThread.length === 0 ? (
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-sm text-slate-400">
            Riwayat chat akan muncul di sini.
          </div>
        ) : (
          chatThread.map((entry) => (
            <Fragment key={entry.id}>
              {entry.role === 'assistant' &&
                Array.isArray(entry.toolTraces) &&
                entry.toolTraces.length > 0 && (
                  <div className="space-y-2">
                    {entry.toolTraces.map((trace, idx) => (
                      <div
                        key={`${entry.id}-trace-${idx}`}
                        className="flex items-start gap-2 rounded-lg border border-amber-500/30 bg-slate-900/70 px-3 py-2 font-mono text-[11px] leading-snug text-amber-100"
                      >
                        <Wrench className="mt-0.5 h-3 w-3 shrink-0 text-amber-400" />
                        <div className="min-w-0">
                          <p className="font-semibold text-amber-300">{trace.tool}</p>
                          <p className="mt-0.5 break-words text-amber-100/80">
                            {String(trace.summary ?? '')}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

              <div
                className={`rounded-xl border p-3 text-sm ${
                  entry.role === 'user'
                    ? 'border-cyan-500/30 bg-cyan-500/10 text-cyan-100'
                    : 'border-emerald-500/20 bg-emerald-500/10 text-emerald-200'
                }`}
              >
                <p className="mb-2 text-[10px] uppercase tracking-[0.18em] opacity-80">
                  {entry.role === 'user' ? 'Anda' : `AI Agent${entry.source ? ` • ${entry.source}` : ''}`}
                </p>
                <p className="whitespace-pre-wrap leading-relaxed">{entry.text}</p>
              </div>
            </Fragment>
          ))
        )}
        {loading && (
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3 text-sm text-emerald-200 animate-pulse">
            AI Agent sedang menyusun jawaban...
          </div>
        )}
      </div>
    </div>
  );
}

export default AgentPanel;
